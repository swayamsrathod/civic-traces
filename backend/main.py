"""Dashboard API and page.

Run:  uvicorn backend.main:app --reload
Then open http://localhost:8000
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analytics.ward_scores import ward_scores  # noqa: E402
from mcp_server.db import connect, init_db, now  # noqa: E402

app = FastAPI(title="CIVIC TRACE API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "dashboard" / "index.html")


@app.get("/complaints")
def complaints():
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.issue_type, c.department, c.status, c.report_count, c.reference_no, c.ward, "
            "c.filed_at, c.created_at, AVG(r.lat) AS lat, AVG(r.lon) AS lon "
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
            "SUM(status='resolved') AS resolved, SUM(status='escalated') AS escalated FROM complaints"
        ).fetchone()
    d = dict(c)
    d["merged"] = d["reports"] - d["complaints"]
    return d


@app.post("/complaints/{cid}/resolve")
def resolve(cid: int):
    with connect() as conn:
        conn.execute("UPDATE complaints SET status='resolved', resolved_at=? WHERE id=?", (now(), cid))
    return {"ok": True}
