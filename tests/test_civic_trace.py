"""End-to-end tests for the CIVIC TRACE tools. Run with:  pytest -q"""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GATE2 = (13.0350, 77.5350)  # sample location in Ward 12


@pytest.fixture()
def server(tmp_path, monkeypatch):
    """A fresh server module with its own empty database and no real emails."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")  # empty, so a local .env key is not used
    import mcp_server.db as db
    importlib.reload(db)
    import mcp_server.server as srv
    importlib.reload(srv)
    return srv


def report(srv, issue="pothole", lat=GATE2[0], lon=GATE2[1]):
    return srv.draft_complaint(issue, "high", "Deep pothole near Gate 2", lat, lon, "Gate 2", "Ward 12")


# ---------- classification ----------

@pytest.mark.parametrize("text,issue", [
    ("Huge pothole near the school gate", "pothole"),
    ("Garbage dumped on the footpath for a week", "garbage"),
    ("Street light not working, road is dark", "streetlight"),
    ("Water pipeline burst and leaking", "water_leak"),
    ("Sewage drain overflowing", "drainage"),
    ("Something is wrong here", "other"),
])
def test_keyword_classifier(server, text, issue):
    assert server.classify_issue(text=text)["issue_type"] == issue


def test_classifier_marks_dangerous_as_high(server):
    assert server.classify_issue(text="Dangerous deep pothole")["severity"] == "high"


def test_classifier_says_when_it_used_fallback(server):
    assert "fallback" in server.classify_issue(text="pothole")["method"]


# ---------- routing ----------

def test_find_authority_routes_by_issue(server):
    assert server.find_authority("garbage")["department"] == "Solid Waste Management"


def test_find_authority_unknown_issue_goes_to_general(server):
    assert server.find_authority("alien_invasion")["department"] == "General Grievances"


# ---------- duplicate merging ----------

def test_same_issue_nearby_is_merged(server):
    first = report(server)
    second = report(server, lat=GATE2[0] + 0.0001)  # about 11 m away
    assert second["merged_with_existing"] is True
    assert second["complaint_id"] == first["complaint_id"]
    assert second["report_count"] == 2


def test_far_away_report_is_not_merged(server):
    first = report(server)
    far = report(server, lat=GATE2[0] + 0.01)  # about 1.1 km away
    assert far["merged_with_existing"] is False
    assert far["complaint_id"] != first["complaint_id"]


def test_different_issue_same_place_is_not_merged(server):
    report(server, "pothole")
    other = report(server, "garbage")
    assert other["merged_with_existing"] is False


# ---------- approval gate ----------

def test_filing_without_approval_is_refused(server):
    cid = report(server)["complaint_id"]
    result = server.file_complaint(cid, user_confirmed=False)
    assert result["filed"] is False
    assert server.track_status(cid)[0]["status"] != "filed"


def test_filing_with_approval_gives_reference(server):
    cid = report(server)["complaint_id"]
    server.ask_user_approval(cid)
    result = server.file_complaint(cid, user_confirmed=True)
    assert result["filed"] is True
    assert result["reference_no"].startswith("CT-")


def test_complaint_cannot_be_filed_twice(server):
    cid = report(server)["complaint_id"]
    server.file_complaint(cid, user_confirmed=True)
    assert server.file_complaint(cid, user_confirmed=True)["filed"] is False


# ---------- follow-up and escalation ----------

def test_escalation_goes_department_then_senior_officer(server):
    cid = report(server)["complaint_id"]
    server.file_complaint(cid, user_confirmed=True)
    first = server.escalate(cid)
    second = server.escalate(cid)
    assert first["level"] == "reminder"
    assert "senior officer" in second["level"]
    assert second["to"] != first["to"]
    assert server.track_status(cid)[0]["status"] == "escalated"


def test_cannot_escalate_unfiled_complaint(server):
    cid = report(server)["complaint_id"]
    assert server.escalate(cid)["sent"] is False


# ---------- accountability scores ----------

def test_ward_scores_rank_slowest_first():
    from analytics.ward_scores import ward_scores
    rows = [
        {"ward": "Ward 3", "status": "resolved", "filed_at": "2026-11-01T10:00:00", "resolved_at": "2026-11-03T10:00:00"},
        {"ward": "Ward 21", "status": "resolved", "filed_at": "2026-11-01T10:00:00", "resolved_at": "2026-11-21T10:00:00"},
    ]
    scores = ward_scores(rows)
    assert [s["ward"] for s in scores] == ["Ward 21", "Ward 3"]
    assert scores[0]["avg_days"] == 20.0
