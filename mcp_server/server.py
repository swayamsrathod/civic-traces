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


# English, Kannada and Hindi (script and romanised), so citizens can report in their own language.
KEYWORDS = {
    "pothole": ["pothole", "crater", "road broken", "damaged road", "hole in the road", "gundi",
                "ಗುಂಡಿ", "ರಸ್ತೆ ಹಾಳ", "गड्ढा", "गड्ढे", "सड़क टूटी", "gaddha", "gadda"],
    "garbage": ["garbage", "trash", "waste", "dump", "litter", "rubbish", "kasa",
                "ಕಸ", "ತ್ಯಾಜ್ಯ", "कचरा", "कूड़ा", "कूडा", "kachra", "kuda"],
    "streetlight": ["streetlight", "street light", "light not working", "dark road", "lamp",
                    "ಬೀದಿ ದೀಪ", "ದೀಪ", "स्ट्रीट लाइट", "बत्ती", "batti"],
    "water_leak": ["leak", "pipe", "pipeline", "water flowing", "burst",
                   "ಸೋರಿಕೆ", "ಪೈಪ್", "लीक", "पाइप", "पानी बह"],
    "drainage": ["drain", "sewage", "sewer", "overflow", "manhole", "flooded",
                 "ಚರಂಡಿ", "ಒಳಚರಂಡಿ", "नाली", "सीवर", "nali", "gutter"],
}
HIGH_WORDS = ["dangerous", "accident", "deep", "huge", "big", "injur", "urgent", "flood", "kids", "school",
              "ಅಪಾಯ", "ಅಪಘಾತ", "ಆಳವಾದ", "ದೊಡ್ಡ", "खतरनाक", "दुर्घटना", "गहरा", "बड़ा", "khatarnak"]


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


def run_due_followups(filed_after: str = "") -> list:
    """Send every follow-up that is due. Called on a timer by the backend, so CIVIC TRACE keeps
    chasing complaints without anyone asking. Stops once a complaint has been escalated.
    filed_after (ISO time) limits it to newer complaints, used in fast demo mode."""
    done = []
    for r in track_status():
        if filed_after and (r["filed_at"] or "") < filed_after:
            continue
        if r["overdue"] and r["status"] == "filed":
            done.append({"complaint_id": r["id"], **escalate(r["id"])})
    return done


# ---------- MCP resources: read-only data any MCP client can browse ----------

@mcp.resource("civictrace://wards/scores", name="ward_scores", mime_type="application/json",
              description="Accountability report card: average days to fix and escalation rate per ward")
def ward_scores_resource() -> str:
    from analytics.ward_scores import ward_scores
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT ward, status, filed_at, resolved_at FROM complaints")]
    return json.dumps(ward_scores(rows), indent=2)


@mcp.resource("civictrace://complaints/open", name="open_complaints", mime_type="application/json",
              description="Complaints that are filed or escalated and not yet fixed")
def open_complaints_resource() -> str:
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, reference_no, issue_type, ward, department, status, report_count, filed_at "
            "FROM complaints WHERE status IN ('filed', 'escalated') ORDER BY filed_at")]
    return json.dumps(rows, indent=2)


@mcp.resource("civictrace://complaints/{complaint_id}", name="complaint_trail", mime_type="application/json",
              description="One complaint with its full audit trail")
def complaint_resource(complaint_id: str) -> str:
    with connect() as conn:
        c = conn.execute("SELECT id, reference_no, issue_type, ward, department, status, report_count, filed_at, "
                         "resolved_at FROM complaints WHERE id=?", (int(complaint_id),)).fetchone()
        if c is None:
            return json.dumps({"error": f"No complaint with id {complaint_id}"})
        events = [dict(r) for r in conn.execute(
            "SELECT at, kind, detail FROM events WHERE complaint_id=? ORDER BY id", (int(complaint_id),))]
    return json.dumps({**dict(c), "events": events}, indent=2)


def draft_rti_request(complaint_id: int, applicant_name: str = "[Your full name]",
                      applicant_address: str = "[Your address, phone and email]") -> dict:
    """Write a Right to Information (RTI Act 2005, Section 6(1)) application asking what action
    was taken on an ignored complaint, using the complaint's own audit trail as the facts."""
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
        if c is None:
            return {"error": f"No complaint with id {complaint_id}"}
        events = {r["kind"]: r["at"] for r in conn.execute(
            "SELECT kind, MIN(at) AS at FROM events WHERE complaint_id=? GROUP BY kind", (complaint_id,))}
    if c["status"] not in ("filed", "escalated") or not c["reference_no"]:
        return {"error": "An RTI request is only useful for a filed complaint that is still unresolved."}
    day = lambda iso: datetime.fromisoformat(iso).strftime("%d %B %Y") if iso else "[date]"
    issue = c["issue_type"].replace("_", " ")
    history = [f"- Complaint {c['reference_no']} about a {issue} in {c['ward']} was filed on {day(c['filed_at'])}."]
    if c["report_count"] > 1:
        history.append(f"- The same issue was reported by {c['report_count']} citizens.")
    if "reminder" in events:
        history.append(f"- A reminder was sent on {day(events['reminder'])}.")
    if "escalated" in events:
        history.append(f"- The complaint was escalated to the senior officer on {day(events['escalated'])}.")
    history.append("- As of the date of this application, the issue has not been resolved.")
    text = f"""To,
The Public Information Officer,
{c['department']},
[Office address of the department]

Subject: Request for information under Section 6(1) of the Right to Information Act, 2005,
regarding civic complaint {c['reference_no']}

Sir / Madam,

Background:
{chr(10).join(history)}

Please provide the following information:
1. The daily progress report or file notings on complaint {c['reference_no']}, with certified copies.
2. The name and designation of the officer responsible for acting on this complaint.
3. The dates on which the complaint, the reminder and the escalation were received, and the action taken on each.
4. The time limit for resolving such complaints under the department's citizen charter or service rules, and the reasons for the delay in this case.
5. The expected date by which the {issue} will be fixed.

I am enclosing the application fee of Rs. 10 (or have paid it online). I am a citizen of India.
Please provide the information within 30 days, as required under Section 7(1) of the Act.

Yours faithfully,
{applicant_name}
{applicant_address}
Date: {datetime.now().strftime("%d %B %Y")}
"""
    return {"complaint_id": complaint_id, "reference_no": c["reference_no"], "rti_text": text,
            "how_to_file": "In Karnataka, file online at https://rtionline.karnataka.gov.in or by post to the department's "
                           "Public Information Officer. Fee Rs. 10. A reply is due within 30 days; if there is none, "
                           "a first appeal can be filed under Section 19(1)."}


@mcp.resource("civictrace://complaints/{complaint_id}/rti", name="rti_request", mime_type="text/plain",
              description="A ready-to-file RTI application for an unresolved complaint")
def rti_resource(complaint_id: str) -> str:
    out = draft_rti_request(int(complaint_id))
    return out.get("rti_text") or out["error"]


# ---------- MCP prompt: a guided workflow clients can offer as a slash command ----------

@mcp.prompt(name="report_civic_issue", description="Report a civic problem and have CIVIC TRACE file and chase it")
def report_civic_issue(description: str, location: str = "") -> str:
    return (
        "You are CIVIC TRACE, an agent that files civic complaints for a citizen and follows them up.\n"
        f"The citizen reports: {description}\n"
        f"Location: {location or 'ask the citizen for the location or landmark'}\n\n"
        "Steps:\n"
        "1. Call classify_issue with the description (and the photo path if one was shared).\n"
        "2. Call draft_complaint with the issue, severity, description, coordinates and landmark. "
        "It routes to the right department and merges duplicate reports automatically.\n"
        "3. Call ask_user_approval and show the citizen the full draft and who it will be sent to.\n"
        "4. Only if the citizen clearly says yes, call file_complaint with user_confirmed=true.\n"
        "5. Tell the citizen the reference number and when CIVIC TRACE will follow up.\n"
        "Never file without an explicit yes."
    )


if __name__ == "__main__":
    # stdio for Claude Desktop (default), or:  python -m mcp_server.server --http  (port 8001)
    if "--http" in sys.argv:
        mcp.run("streamable-http", host="0.0.0.0", port=int(os.getenv("MCP_PORT", "8001")))
    else:
        mcp.run()
