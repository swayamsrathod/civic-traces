"""CIVIC TRACE MCP server.

Run:  python -m mcp_server.server
Then connect it to an MCP client (for example Claude Desktop) as a stdio server.
"""
import base64
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from analytics.duplicates import find_nearby_duplicate  # noqa: E402
from automation.emailer import send_email  # noqa: E402
from mcp_server.db import connect, init_db, log_event, now  # noqa: E402

mcp = MCPServer("civic-trace")
init_db()

ISSUE_TYPES = ["pothole", "garbage", "streetlight", "water_leak", "drainage", "other"]
ESCALATION_DAYS = float(os.getenv("ESCALATION_DAYS", "3"))
# Demo mode: set ESCALATION_MINUTES (e.g. 1) to watch follow-ups happen live.
ESCALATION_DELTA = (timedelta(minutes=float(os.environ["ESCALATION_MINUTES"])) if os.getenv("ESCALATION_MINUTES")
                    else timedelta(days=ESCALATION_DAYS))


def follow_up_label():
    m = ESCALATION_DELTA.total_seconds() / 60
    return f"{m:g} minute(s)" if m < 60 * 24 else f"{m / 1440:g} day(s)"


def nearest_ward(lat: float, lon: float) -> str:
    """Pick the ward whose centre is closest (data/wards.csv)."""
    with open(ROOT / "data" / "wards.csv", newline="") as f:
        wards = list(csv.DictReader(f))
    return min(wards, key=lambda w: (float(w["lat"]) - lat) ** 2 + (float(w["lon"]) - lon) ** 2)["ward"]


def _load_authorities():
    with open(ROOT / "data" / "authorities.csv", newline="") as f:
        return list(csv.DictReader(f))


@mcp.tool()
def classify_issue(image_path: str = "", text: str = "") -> dict:
    """Identify the civic issue from a photo and/or text.
    Returns issue_type (one of pothole, garbage, streetlight, water_leak, drainage, other),
    severity (low, medium, high) and a one-line description.
    Without an ANTHROPIC_API_KEY it falls back to keyword matching on the text."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {**classify_text(text), "method": "keyword fallback (no API key set)"}
    try:
        out = _classify_with_claude(image_path, text)
        if out.get("issue_type") not in ISSUE_TYPES:
            out["issue_type"] = "other"
        return {**out, "method": "claude"}
    except Exception as e:  # network error, bad key, unparseable reply
        return {**classify_text(text), "method": f"keyword fallback ({type(e).__name__})"}


KEYWORDS = {
    "pothole": ["pothole", "crater", "road broken", "damaged road", "hole in the road", "gundi"],
    "garbage": ["garbage", "trash", "waste", "dump", "litter", "rubbish", "kasa"],
    "streetlight": ["streetlight", "street light", "light not working", "dark road", "lamp"],
    "water_leak": ["leak", "pipe", "pipeline", "water flowing", "burst"],
    "drainage": ["drain", "sewage", "sewer", "overflow", "manhole", "flooded"],
}
HIGH_WORDS = ["dangerous", "accident", "deep", "huge", "big", "injur", "urgent", "flood", "kids", "school"]


def classify_text(text: str) -> dict:
    """Simple keyword classifier used when Claude is not available."""
    t = (text or "").lower()
    issue = next((k for k, words in KEYWORDS.items() if any(w in t for w in words)), "other")
    severity = "high" if any(w in t for w in HIGH_WORDS) else "medium"
    return {"issue_type": issue, "severity": severity, "description": (text or "Civic issue reported").strip()[:160]}


def _classify_with_claude(image_path: str, text: str) -> dict:
    import anthropic

    content = []
    if image_path:
        data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        media = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        content.append({"type": "image", "source": {"type": "base64", "media_type": media, "data": data}})
    content.append({
        "type": "text",
        "text": (
            f"Classify this civic issue. User note: {text or 'none'}.\n"
            f"Reply with JSON only: {{\"issue_type\": one of {ISSUE_TYPES}, "
            "\"severity\": \"low|medium|high\", \"description\": \"one short sentence\"}"
        ),
    })
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=300,
        messages=[{"role": "user", "content": content}],
    )
    raw = msg.content[0].text.strip().strip("`").removeprefix("json").strip()
    return json.loads(raw)


@mcp.tool()
def find_authority(issue_type: str, ward: str = "*") -> dict:
    """Find the department and contact responsible for an issue type in a ward."""
    rows = _load_authorities()
    for r in rows:
        if r["issue_type"] == issue_type and r["ward"] in (ward, "*"):
            return r
    return next(r for r in rows if r["issue_type"] == "other")


@mcp.tool()
def check_duplicates(issue_type: str, lat: float, lon: float, radius_m: int = 50) -> dict:
    """Check whether the same issue was already reported within radius_m metres.
    Returns the existing complaint id and how many people reported it, if any."""
    with connect() as conn:
        existing = [dict(r) for r in conn.execute("SELECT * FROM reports WHERE complaint_id IS NOT NULL")]
    match = find_nearby_duplicate({"issue_type": issue_type, "lat": lat, "lon": lon}, existing, radius_m)
    if not match:
        return {"duplicate": False}
    with connect() as conn:
        c = conn.execute("SELECT id, report_count, status FROM complaints WHERE id=?", (match["complaint_id"],)).fetchone()
    return {"duplicate": True, "complaint_id": c["id"], "report_count": c["report_count"], "status": c["status"]}


@mcp.tool()
def draft_complaint(issue_type: str, severity: str, description: str, lat: float, lon: float,
                    location_name: str = "", ward: str = "*", photo_path: str = "") -> dict:
    """Save the report and draft a formal complaint. If the same issue was already reported
    nearby, the report joins that complaint and the count goes up instead."""
    dup = check_duplicates(issue_type, lat, lon)
    auth = find_authority(issue_type, ward)
    with connect() as conn:
        if dup["duplicate"]:
            cid = dup["complaint_id"]
            conn.execute("UPDATE complaints SET report_count = report_count + 1 WHERE id=?", (cid,))
            log_event(conn, cid, "merged", "Another citizen reported the same issue nearby")
        else:
            cur = conn.execute(
                "INSERT INTO complaints (issue_type, department, authority_email, escalation_email, ward, status, created_at) "
                "VALUES (?,?,?,?,?, 'draft', ?)",
                (issue_type, auth["department"], auth["authority_email"], auth["escalation_email"], ward, now()),
            )
            cid = cur.lastrowid
            log_event(conn, cid, "reported", f"{issue_type.replace('_', ' ').title()} reported ({severity} severity)")
        conn.execute(
            "INSERT INTO reports (issue_type, severity, description, lat, lon, ward, complaint_id, photo_path, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (issue_type, severity, description, lat, lon, ward, cid, photo_path or None, now()),
        )
        count = conn.execute("SELECT report_count FROM complaints WHERE id=?", (cid,)).fetchone()[0]
        place = location_name or f"{lat:.5f}, {lon:.5f}"
        draft = (
            f"To the {auth['department']} Department,\n\n"
            f"Subject: {issue_type.replace('_', ' ').title()} at {place} ({severity} severity)\n\n"
            f"This is to report the following issue: {description}\n"
            f"Location: {place} (https://maps.google.com/?q={lat},{lon})\n"
            f"Reported by {count} citizen(s) through CIVIC TRACE.\n\n"
            "We request that this be inspected and resolved at the earliest, and that a reference "
            "number be shared for tracking.\n\nRegards,\nCIVIC TRACE on behalf of the reporting citizens"
        )
        conn.execute("UPDATE complaints SET draft=? WHERE id=?", (draft, cid))
    return {"complaint_id": cid, "merged_with_existing": dup["duplicate"], "report_count": count, "draft": draft}


@mcp.tool()
def ask_user_approval(complaint_id: int) -> dict:
    """Show the draft complaint to the citizen. The agent MUST display this draft and get
    an explicit 'yes' from the user before calling file_complaint."""
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
        if c is None:
            return {"error": f"No complaint with id {complaint_id}"}
        conn.execute("UPDATE complaints SET status='pending_approval' WHERE id=? AND status='draft'", (complaint_id,))
    return {
        "complaint_id": complaint_id,
        "send_to": c["authority_email"],
        "draft": c["draft"],
        "instruction": "Show this to the user and ask: 'Shall I file this complaint?' Only call file_complaint after they say yes.",
    }


@mcp.tool()
def file_complaint(complaint_id: int, user_confirmed: bool, method: str = "email") -> dict:
    """File an approved complaint. method is 'email' or 'portal'.
    Refuses unless user_confirmed is true."""
    if not user_confirmed:
        return {"filed": False, "reason": "User has not approved this complaint."}
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
    if c is None:
        return {"filed": False, "reason": f"No complaint with id {complaint_id}"}
    if c["status"] in ("filed", "escalated", "resolved"):
        return {"filed": False, "reason": f"Already {c['status']}", "reference_no": c["reference_no"]}

    if method == "portal":
        from automation.portal_filer import file_on_portal
        lines = c["draft"].splitlines()
        location = next((l.split(": ", 1)[1] for l in lines if l.startswith("Location:")), "")
        ref = file_on_portal(c["department"], c["issue_type"], location, c["draft"])
    else:
        ref = f"CT-{complaint_id:04d}"
        send_email(c["authority_email"], f"[{ref}] Civic complaint: {c['issue_type']}", c["draft"])

    with connect() as conn:
        conn.execute("UPDATE complaints SET status='filed', reference_no=?, filed_at=? WHERE id=?", (ref, now(), complaint_id))
        log_event(conn, complaint_id, "filed", f"Filed with {c['department']} by {'grievance portal' if method == 'portal' else 'email'}. Reference {ref}")
    return {"filed": True, "reference_no": ref, "method": method, "follow_up_in": follow_up_label()}


@mcp.tool()
def track_status(complaint_id: int = 0) -> list:
    """Show the status of one complaint, or of all complaints if complaint_id is 0.
    Flags complaints that are overdue for follow-up."""
    with connect() as conn:
        q = "SELECT id, issue_type, department, status, reference_no, report_count, filed_at, last_followup_at FROM complaints"
        rows = [dict(r) for r in (conn.execute(q + " WHERE id=?", (complaint_id,)) if complaint_id else conn.execute(q))]
    for r in rows:
        last = r["last_followup_at"] or r["filed_at"]
        r["overdue"] = bool(
            r["status"] in ("filed", "escalated") and last
            and datetime.now() - datetime.fromisoformat(last) > ESCALATION_DELTA
        )
    return rows


@mcp.tool()
def escalate(complaint_id: int) -> dict:
    """Send a follow-up for an ignored complaint. The first follow-up goes to the department;
    the next goes to the senior officer and marks the complaint as escalated."""
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
    if c is None:
        return {"sent": False, "reason": f"No complaint with id {complaint_id}"}
    if c["status"] not in ("filed", "escalated"):
        return {"sent": False, "reason": f"Complaint is {c['status']}"}
    first = c["last_followup_at"] is None
    to = c["authority_email"] if first else c["escalation_email"]
    body = (
        f"Follow-up on complaint {c['reference_no']} ({c['issue_type']}), filed on {c['filed_at'][:10]} "
        f"and reported by {c['report_count']} citizen(s). The issue is still unresolved. "
        "Kindly share the current status and expected date of resolution.\n\n" + c["draft"]
    )
    send_email(to, f"[{c['reference_no']}] Follow-up: unresolved civic complaint", body)
    with connect() as conn:
        conn.execute(
            "UPDATE complaints SET last_followup_at=?, status=? WHERE id=?",
            (now(), "filed" if first else "escalated", complaint_id),
        )
        log_event(conn, complaint_id, "reminder" if first else "escalated",
                  "Reminder sent to the department" if first else "Escalated to the senior officer")
    return {"sent": True, "to": to, "level": "reminder" if first else "escalated to senior officer"}


def resolve_complaint(complaint_id: int, note: str = "") -> dict:
    """Mark a complaint as fixed (used by the department) and notify every citizen who reported it."""
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
        if c is None:
            return {"resolved": False, "reason": f"No complaint with id {complaint_id}"}
        if c["status"] == "resolved":
            return {"resolved": False, "reason": "Already resolved"}
        conn.execute("UPDATE complaints SET status='resolved', resolved_at=? WHERE id=?", (now(), complaint_id))
        log_event(conn, complaint_id, "resolved", note or "Marked fixed by the department")
        log_event(conn, complaint_id, "notified", f"All {c['report_count']} reporter(s) notified")
    return {"resolved": True, "reporters_notified": c["report_count"]}


def run_due_followups() -> list:
    """Send every follow-up that is due. Called on a timer by the backend, so CIVIC TRACE keeps
    chasing complaints without anyone asking. Stops once a complaint has been escalated."""
    done = []
    for r in track_status():
        if r["overdue"] and r["status"] == "filed":
            done.append({"complaint_id": r["id"], **escalate(r["id"])})
    return done


if __name__ == "__main__":
    mcp.run()
