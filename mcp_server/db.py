"""SQLite storage for reports and complaints."""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "civictrace.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_type TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                ward TEXT,
                complaint_id INTEGER,
                photo_path TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                at TEXT NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT
            );
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_type TEXT NOT NULL,
                department TEXT,
                authority_email TEXT,
                escalation_email TEXT,
                ward TEXT,
                draft TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                reference_no TEXT,
                report_count INTEGER NOT NULL DEFAULT 1,
                filed_at TEXT,
                last_followup_at TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        # Upgrade databases created before photos were supported
        cols = [r[1] for r in conn.execute("PRAGMA table_info(reports)")]
        if "photo_path" not in cols:
            conn.execute("ALTER TABLE reports ADD COLUMN photo_path TEXT")


def log_event(conn, complaint_id, kind, detail=""):
    """Append one line to a complaint's audit trail."""
    conn.execute("INSERT INTO events (complaint_id, at, kind, detail) VALUES (?,?,?,?)",
                 (complaint_id, now(), kind, detail))


def now():
    return datetime.now().isoformat(timespec="seconds")
