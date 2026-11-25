"""Fill the database with realistic demo complaints around Bengaluru, so the
dashboard has something to show. Run once:  python -m scripts.seed_demo
Use --reset to wipe existing data first."""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_server.db import DB_PATH, connect, init_db  # noqa: E402


def event(conn, cid, at, kind, detail):
    conn.execute("INSERT INTO events (complaint_id, at, kind, detail) VALUES (?,?,?,?)", (cid, at.isoformat(timespec="seconds"), kind, detail))

random.seed(7)

# ward: (centre lat, lon, how slow the department is in days)
WARDS = {
    "Ward 3": (13.0280, 77.5190, 4),
    "Ward 7": (13.0450, 77.5000, 6),
    "Ward 12": (13.0350, 77.5350, 12),
    "Ward 15": (13.0150, 77.5450, 9),
    "Ward 21": (13.0550, 77.5250, 30),
}
ISSUES = {
    "pothole": "Roads and Infrastructure",
    "garbage": "Solid Waste Management",
    "streetlight": "Electrical (Streetlights)",
    "water_leak": "Water Supply and Sewerage",
}
DESC = {
    "pothole": "Deep pothole on the main road, dangerous for two-wheelers",
    "garbage": "Garbage pile not cleared, spreading onto the footpath",
    "streetlight": "Streetlight not working, road completely dark at night",
    "water_leak": "Pipeline leaking, water flowing on the road",
}


def main():
    if "--reset" in sys.argv and Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
    init_db()
    now = datetime.now()
    with connect() as conn:
        n = 0
        for ward, (lat, lon, slow) in WARDS.items():
            for _ in range(random.randint(5, 8)):
                issue = random.choice(list(ISSUES))
                clat, clon = lat + random.uniform(-0.008, 0.008), lon + random.uniform(-0.008, 0.008)
                count = random.choice([1, 1, 2, 3, 5, 8, 12, 23])
                filed = now - timedelta(days=random.uniform(1, 40), hours=random.uniform(0, 12))
                age = (now - filed).days
                fix_time = max(1, random.gauss(slow, slow * 0.3))
                if fix_time < age:
                    status, resolved = "resolved", filed + timedelta(days=fix_time)
                elif age > 6:
                    status, resolved = "escalated", None
                else:
                    status, resolved = "filed", None
                cur = conn.execute(
                    "INSERT INTO complaints (issue_type, department, authority_email, escalation_email, ward, draft, status, "
                    "reference_no, report_count, filed_at, last_followup_at, resolved_at, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (issue, ISSUES[issue], "demo@example-city.gov.in", "chief@example-city.gov.in", ward,
                     DESC[issue], status, None, count, filed.isoformat(timespec="seconds"),
                     (filed + timedelta(days=3)).isoformat(timespec="seconds") if status == "escalated" else None,
                     resolved.isoformat(timespec="seconds") if resolved else None, filed.isoformat(timespec="seconds")),
                )
                cid = cur.lastrowid
                conn.execute("UPDATE complaints SET reference_no=? WHERE id=?", (f"CT-{cid:04d}", cid))
                event(conn, cid, filed - timedelta(minutes=5), "reported", f"{issue.replace('_', ' ').title()} reported")
                if count > 1:
                    event(conn, cid, filed - timedelta(minutes=2), "merged", f"{count - 1} more citizen report(s) merged")
                event(conn, cid, filed, "filed", f"Filed with {ISSUES[issue]} by email. Reference CT-{cid:04d}")
                if status == "escalated" or (resolved and fix_time > 3):
                    event(conn, cid, filed + timedelta(days=3), "reminder", "Reminder sent to the department")
                if status == "escalated":
                    event(conn, cid, filed + timedelta(days=6), "escalated", "Escalated to the senior officer")
                if resolved:
                    event(conn, cid, resolved, "resolved", "Marked fixed by the department")
                    event(conn, cid, resolved, "notified", f"All {count} reporter(s) notified")
                for _ in range(count):
                    conn.execute(
                        "INSERT INTO reports (issue_type, severity, description, lat, lon, ward, complaint_id, created_at) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (issue, random.choice(["medium", "high"]), DESC[issue],
                         clat + random.uniform(-0.0002, 0.0002), clon + random.uniform(-0.0002, 0.0002),
                         ward, cid, filed.isoformat(timespec="seconds")),
                    )
                n += 1
    print(f"Seeded {n} demo complaints into {DB_PATH}")


if __name__ == "__main__":
    main()
