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
                created_at TEXT NOT NULL
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


def now():
    return datetime.now().isoformat(timespec="seconds")
