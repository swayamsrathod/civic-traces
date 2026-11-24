"""Dashboard API: complaints for the map and ward accountability scores.

Run:  uvicorn backend.main:app --reload
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analytics.ward_scores import ward_scores  # noqa: E402
from mcp_server.db import connect, init_db  # noqa: E402

app = FastAPI(title="CIVIC TRACE API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()


@app.get("/complaints")
def complaints():
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.issue_type, c.status, c.report_count, c.reference_no, c.ward, "
            "AVG(r.lat) AS lat, AVG(r.lon) AS lon FROM complaints c JOIN reports r ON r.complaint_id = c.id GROUP BY c.id"
        )
        return [dict(r) for r in rows]


@app.get("/wards")
def wards():
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT ward, status, filed_at, resolved_at FROM complaints")]
    return ward_scores(rows)


@app.post("/complaints/{cid}/resolve")
def resolve(cid: int):
    from mcp_server.db import now
    with connect() as conn:
        conn.execute("UPDATE complaints SET status='resolved', resolved_at=? WHERE id=?", (now(), cid))
    return {"ok": True}
