"""Tests for the web app: report page flow, tracking, department and automatic follow-ups."""
import importlib
import io
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")
SPOT = {"lat": "13.0350", "lon": "77.5350", "location_name": "Gate 2"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "web.db"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("FOLLOWUP_CHECK_SECONDS", "0")   # no background loop in tests
    monkeypatch.setenv("ESCALATION_MINUTES", "0.001")   # follow-ups due almost at once
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("DRY_RUN", "true")
    import mcp_server.db as db
    importlib.reload(db)
    import mcp_server.server as srv
    importlib.reload(srv)
    import backend.main as main
    importlib.reload(main)
    with TestClient(main.app) as c:
        c.tools = srv
        yield c


def report(client, desc="Deep dangerous pothole near Gate 2", photo=False, **where):
    files = {"photo": ("pothole.png", io.BytesIO(PNG), "image/png")} if photo else None
    return client.post("/api/report", data={"description": desc, **SPOT, **where}, files=files)


def test_pages_are_served(client):
    for path, text in (("/", "Accountability"), ("/report", "Report a civic issue"),
                       ("/track", "Track a complaint"), ("/department", "Department view")):
        r = client.get(path)
        assert r.status_code == 200 and text in r.text


def test_report_runs_agent_steps_and_waits_for_approval(client):
    d = report(client).json()
    assert [s["tool"] for s in d["steps"]] == ["classify_issue", "find_authority", "check_duplicates", "draft_complaint"]
    assert d["classification"]["issue_type"] == "pothole"
    assert d["ward"] == "Ward 12"
    assert d["status"] == "pending_approval" and d["reference_no"] is None
    assert "Roads and Infrastructure" in d["draft"]


def test_report_needs_photo_or_description(client):
    assert report(client, desc="").status_code == 400


def test_photo_is_saved_and_shown(client):
    d = report(client, photo=True).json()
    detail = client.get(f"/api/complaints/{d['complaint_id']}").json()
    assert len(detail["photos"]) == 1
    assert client.get(detail["photos"][0]).status_code == 200


def test_bad_file_type_is_rejected(client):
    files = {"photo": ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    assert client.post("/api/report", data={"description": "x", **SPOT}, files=files).status_code == 400


def test_filing_needs_confirmation(client):
    cid = report(client).json()["complaint_id"]
    assert client.post(f"/api/complaints/{cid}/file", json={"confirmed": False}).json()["filed"] is False
    filed = client.post(f"/api/complaints/{cid}/file", json={"confirmed": True}).json()
    assert filed["filed"] is True and filed["reference_no"].startswith("CT-")


def test_second_report_joins_filed_complaint(client):
    cid = report(client).json()["complaint_id"]
    ref = client.post(f"/api/complaints/{cid}/file", json={"confirmed": True}).json()["reference_no"]
    again = report(client, desc="Big pothole at gate", lat="13.03505").json()
    assert again["complaint_id"] == cid and again["merged"] is True
    assert again["reference_no"] == ref and again["report_count"] == 2


def test_lookup_by_reference(client):
    cid = report(client).json()["complaint_id"]
    ref = client.post(f"/api/complaints/{cid}/file", json={"confirmed": True}).json()["reference_no"]
    assert client.get("/api/lookup", params={"ref": ref.lower()}).json()["id"] == cid
    assert client.get("/api/lookup", params={"ref": "CT-9999"}).status_code == 404


def test_automatic_followups_remind_then_escalate_then_stop(client):
    cid = report(client).json()["complaint_id"]
    client.post(f"/api/complaints/{cid}/file", json={"confirmed": True})
    time.sleep(0.1)
    assert client.tools.run_due_followups()[0]["level"] == "reminder"
    time.sleep(0.1)
    assert "senior officer" in client.tools.run_due_followups()[0]["level"]
    time.sleep(0.1)
    assert client.tools.run_due_followups() == []   # stops after escalation
    kinds = [e["kind"] for e in client.get(f"/api/complaints/{cid}").json()["events"]]
    assert kinds == ["reported", "filed", "reminder", "escalated"]


def test_department_resolves_and_notifies(client):
    cid = report(client).json()["complaint_id"]
    client.post(f"/api/complaints/{cid}/file", json={"confirmed": True})
    assert client.post(f"/complaints/{cid}/resolve").json()["resolved"] is True
    detail = client.get(f"/api/complaints/{cid}").json()
    assert detail["status"] == "resolved"
    assert [e["kind"] for e in detail["events"]][-2:] == ["resolved", "notified"]
    assert client.get("/stats").json()["resolved"] == 1


def test_contact_emails_are_not_exposed(client):
    cid = report(client).json()["complaint_id"]
    detail = client.get(f"/api/complaints/{cid}").json()
    assert "authority_email" not in detail and "escalation_email" not in detail
