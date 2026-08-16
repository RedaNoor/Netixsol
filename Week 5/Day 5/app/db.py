import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import settings

@contextmanager
def connection():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db() -> None:
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS service_catalog (
            project_type TEXT PRIMARY KEY,
            base_price INTEGER NOT NULL,
            min_weeks INTEGER NOT NULL,
            description TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS proposals (
            request_id TEXT PRIMARY KEY,
            client_email TEXT NOT NULL,
            request_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            status TEXT NOT NULL,
            reviewer_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        rows = [
            ("ai_agent", 5000, 4, "Agent workflow, tools, guardrails, evaluation and API integration"),
            ("web_app", 4000, 4, "Full-stack web application delivery"),
            ("api_integration", 2500, 2, "Third-party API and backend integration"),
            ("data_dashboard", 3000, 3, "Data ingestion, metrics and dashboard development"),
            ("other", 3500, 3, "Custom software discovery and implementation"),
        ]
        conn.executemany("INSERT OR IGNORE INTO service_catalog VALUES (?, ?, ?, ?)", rows)

def get_service(project_type: str) -> dict:
    with connection() as conn:
        row = conn.execute("SELECT * FROM service_catalog WHERE project_type = ?", (project_type,)).fetchone()
        if not row:
            raise LookupError(f"Unknown project type: {project_type}")
        return dict(row)

def save_pending(request_id: str, client_email: str, request_data: dict, result_data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO proposals
        (request_id, client_email, request_json, result_json, status, reviewer_notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'pending_approval', '', ?, ?)
        """, (request_id, client_email, json.dumps(request_data), json.dumps(result_data), now, now))

def get_proposal(request_id: str) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE request_id = ?", (request_id,)).fetchone()
        return dict(row) if row else None

def list_pending() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM proposals WHERE status = 'pending_approval' ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def update_approval(request_id: str, approved: bool, reviewer_notes: str) -> dict | None:
    status = "approved" if approved else "rejected"
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        row = conn.execute("SELECT result_json FROM proposals WHERE request_id = ?", (request_id,)).fetchone()
        if not row:
            return None
        result = json.loads(row["result_json"])
        result["status"] = status
        result["reviewer_notes"] = reviewer_notes
        conn.execute(
            "UPDATE proposals SET result_json=?, status=?, reviewer_notes=?, updated_at=? WHERE request_id=?",
            (json.dumps(result), status, reviewer_notes, now, request_id),
        )
        return result
