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
    for path, text in (("/", "Accountability"), ("/report", 'data-i18n="r_title"'),
                       ("/track", 'data-i18n="t_title"'), ("/department", "Department view")):
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


# ---------- remote MCP over HTTP ----------

MCP_H = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
         "mcp-protocol-version": "2025-06-18"}


def rpc(client, method, params=None, id_=1):
    r = client.post("/mcp", headers=MCP_H, json={"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}})
    assert r.status_code == 200, r.text
    return r.json()["result"]


def test_mcp_endpoint_lists_tools_resources_and_prompt(client):
    rpc(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "judge", "version": "1"}})
    tools = [t["name"] for t in rpc(client, "tools/list")["tools"]]
    assert len(tools) == 8 and "file_complaint" in tools and "ask_user_approval" in tools
    uris = [r["uri"] for r in rpc(client, "resources/list")["resources"]]
    assert "civictrace://wards/scores" in uris
    assert [p["name"] for p in rpc(client, "prompts/list")["prompts"]] == ["report_civic_issue"]


def test_mcp_tool_call_over_http(client):
    out = rpc(client, "tools/call", {"name": "classify_issue", "arguments": {"text": "Garbage dumped near the bus stop"}})
    assert out["isError"] is False
    assert '"issue_type": "garbage"' in out["content"][0]["text"]


# ---------- languages ----------

@pytest.mark.parametrize("text,issue", [
    ("ಮುಖ್ಯ ರಸ್ತೆಯಲ್ಲಿ ಆಳವಾದ ಗುಂಡಿ", "pothole"),
    ("ಬಸ್ ನಿಲ್ದಾಣದ ಬಳಿ ಕಸ ಸುರಿಯಲಾಗಿದೆ", "garbage"),
    ("गेट के पास गहरा गड्ढा है", "pothole"),
    ("नाली बंद है, पानी भर गया", "drainage"),
    ("yahan bahut kachra hai", "garbage"),
])
def test_kannada_and_hindi_reports(client, text, issue):
    assert client.tools.classify_text(text)["issue_type"] == issue


# ---------- RTI ----------

def test_rti_only_for_filed_unresolved_complaints(client):
    cid = report(client).json()["complaint_id"]
    assert client.get(f"/api/complaints/{cid}/rti").status_code == 400   # not filed yet


def test_rti_draft_uses_the_audit_trail(client):
    cid = report(client).json()["complaint_id"]
    ref = client.post(f"/api/complaints/{cid}/file", json={"confirmed": True}).json()["reference_no"]
    time.sleep(0.1); client.tools.run_due_followups()
    time.sleep(0.1); client.tools.run_due_followups()
    d = client.get(f"/api/complaints/{cid}/rti", params={"name": "Swayam S Rathod"}).json()
    text = d["rti_text"]
    assert "Section 6(1) of the Right to Information Act, 2005" in text
    assert ref in text and "Roads and Infrastructure" in text
    assert "reminder was sent" in text and "escalated to the senior officer" in text
    assert "Swayam S Rathod" in text and "Section 7(1)" in text


def test_auto_seed_fills_an_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "u"))
    monkeypatch.setenv("AUTO_SEED", "true")
    monkeypatch.setenv("FOLLOWUP_CHECK_SECONDS", "0")
    import mcp_server.db as db
    importlib.reload(db)
    import mcp_server.server as srv
    importlib.reload(srv)
    import scripts.seed_demo as seed
    importlib.reload(seed)
    import backend.main as main
    importlib.reload(main)
    with TestClient(main.app) as c:
        assert c.get("/stats").json()["complaints"] > 20
