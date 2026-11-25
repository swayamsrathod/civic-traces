"""CIVIC TRACE web app: citizen report page, tracking, department view and dashboard.

Run:  python -m uvicorn backend.main:app --reload
Then open http://localhost:8000
"""
import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analytics.ward_scores import ward_scores  # noqa: E402
from mcp_server import server as tools  # noqa: E402
from mcp_server.db import connect, init_db  # noqa: E402

UPLOADS = Path(os.getenv("UPLOADS_DIR", ROOT / "uploads"))
UPLOADS.mkdir(parents=True, exist_ok=True)
CHECK_EVERY = int(os.getenv("FOLLOWUP_CHECK_SECONDS", "30"))
PAGES = ROOT / "dashboard"


async def followup_loop():
    """Keep chasing complaints on a timer, with no one having to ask."""
    while True:
        try:
            done = await asyncio.to_thread(tools.run_due_followups)
            for d in done:
                print(f"[follow-up] complaint {d['complaint_id']}: {d.get('level', d.get('reason'))}")
        except Exception as e:  # never let the loop die
            print(f"[follow-up] error: {e}")
        await asyncio.sleep(CHECK_EVERY)


@asynccontextmanager
async def lifespan(app):
    init_db()
    task = asyncio.create_task(followup_loop()) if CHECK_EVERY > 0 else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="CIVIC TRACE", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")
app.mount("/static", StaticFiles(directory=ROOT / "dashboard"), name="static")


# ---------- pages ----------

@app.get("/")
def dashboard_page():
    return FileResponse(PAGES / "index.html")


@app.get("/report")
def report_page():
    return FileResponse(PAGES / "report.html")


@app.get("/track")
def track_page():
    return FileResponse(PAGES / "track.html")


@app.get("/department")
def department_page():
    return FileResponse(PAGES / "department.html")


# ---------- citizen flow ----------

@app.post("/api/report")
async def create_report(description: str = Form(""), lat: float = Form(...), lon: float = Form(...),
                        location_name: str = Form(""), photo: UploadFile | None = File(None)):
    """Run the agent's steps for one report and return the draft for approval."""
    if not description.strip() and not (photo and photo.filename):
        raise HTTPException(400, "Add a photo or a description.")
    photo_rel = ""
    if photo and photo.filename:
        ext = Path(photo.filename).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            raise HTTPException(400, "Photo must be a JPG, PNG or WEBP image.")
        data = await photo.read()
        if len(data) > 8 * 1024 * 1024:
            raise HTTPException(400, "Photo must be under 8 MB.")
        name = f"{uuid.uuid4().hex}{ext}"
        (UPLOADS / name).write_bytes(data)
        photo_rel = f"/uploads/{name}"

    steps = []
    cls = await asyncio.to_thread(tools.classify_issue, str(UPLOADS / photo_rel.split("/")[-1]) if photo_rel else "", description)
    steps.append({"tool": "classify_issue", "result": f"{cls['issue_type'].replace('_', ' ').title()} · {cls['severity']} severity",
                  "note": cls.get("method", "")})
    ward = tools.nearest_ward(lat, lon)
    auth = tools.find_authority(cls["issue_type"], ward)
    steps.append({"tool": "find_authority", "result": f"{auth['department']} · {ward}"})
    dup = tools.check_duplicates(cls["issue_type"], lat, lon)
    steps.append({"tool": "check_duplicates",
                  "result": f"Joins {dup['report_count']} earlier report(s)" if dup["duplicate"] else "No earlier report nearby"})
    draft = tools.draft_complaint(cls["issue_type"], cls["severity"], cls["description"] or description, lat, lon,
                                  location_name, ward, photo_rel)
    steps.append({"tool": "draft_complaint", "result": f"Draft ready · {draft['report_count']} citizen report(s)"})
    approval = tools.ask_user_approval(draft["complaint_id"])
    with connect() as conn:
        c = dict(conn.execute("SELECT status, reference_no FROM complaints WHERE id=?", (draft["complaint_id"],)).fetchone())
    return {"complaint_id": draft["complaint_id"], "steps": steps, "classification": cls, "ward": ward,
            "department": auth["department"], "send_to": approval["send_to"], "draft": approval["draft"],
            "report_count": draft["report_count"], "merged": draft["merged_with_existing"],
            "status": c["status"], "reference_no": c["reference_no"]}


class FileRequest(BaseModel):
    confirmed: bool
    method: str = "email"


@app.post("/api/complaints/{cid}/file")
def file_complaint(cid: int, req: FileRequest):
    if req.method not in ("email", "portal"):
        raise HTTPException(400, "method must be email or portal")
    return tools.file_complaint(cid, user_confirmed=req.confirmed, method=req.method)


@app.get("/api/complaints/{cid}")
def complaint_detail(cid: int):
    with connect() as conn:
        c = conn.execute("SELECT * FROM complaints WHERE id=?", (cid,)).fetchone()
        if c is None:
            raise HTTPException(404, "Complaint not found")
        events = [dict(r) for r in conn.execute("SELECT at, kind, detail FROM events WHERE complaint_id=? ORDER BY id", (cid,))]
        photos = [r[0] for r in conn.execute("SELECT photo_path FROM reports WHERE complaint_id=? AND photo_path IS NOT NULL", (cid,))]
    d = dict(c)
    d.pop("authority_email"), d.pop("escalation_email")
    return {**d, "events": events, "photos": photos, "follow_up_every": tools.follow_up_label()}


@app.get("/api/lookup")
def lookup(ref: str):
    """Find a complaint by its reference number (CT-0001 or GRV-123456)."""
    with connect() as conn:
        r = conn.execute("SELECT id FROM complaints WHERE reference_no=?", (ref.strip().upper(),)).fetchone()
    if r is None:
        raise HTTPException(404, "No complaint with that reference")
    return {"id": r[0]}


# ---------- department ----------

@app.post("/complaints/{cid}/resolve")
def resolve(cid: int):
    return tools.resolve_complaint(cid)


# ---------- dashboard data ----------

@app.get("/complaints")
def complaints():
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.issue_type, c.department, c.status, c.report_count, c.reference_no, c.ward, "
            "c.filed_at, c.created_at, c.last_followup_at, AVG(r.lat) AS lat, AVG(r.lon) AS lon, MAX(r.photo_path) AS photo "
            "FROM complaints c JOIN reports r ON r.complaint_id = c.id "
            "GROUP BY c.id ORDER BY c.created_at DESC"
        )
        return [dict(r) for r in rows]


@app.get("/wards")
def wards():
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT ward, status, filed_at, resolved_at FROM complaints")]
    return ward_scores(rows)


@app.get("/stats")
def stats():
    with connect() as conn:
        c = conn.execute(
            "SELECT COUNT(*) AS complaints, COALESCE(SUM(report_count), 0) AS reports, "
            "COALESCE(SUM(status='resolved'), 0) AS resolved, COALESCE(SUM(status='escalated'), 0) AS escalated FROM complaints"
        ).fetchone()
    d = dict(c)
    d["merged"] = d["reports"] - d["complaints"]
    return d
