from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

DB_PATH = Path("./orchestrator.sqlite").resolve()


@dataclass
class RunRecord:
    run_id: str
    state: Dict[str, Any]
    status: str  # running|completed|failed
    error: Optional[str] = None


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            state_json TEXT NOT NULL,
            error TEXT
        );
        """
    )
    return conn


def save_run(record: RunRecord) -> None:
    conn = _conn()
    with conn:
        conn.execute(
            "REPLACE INTO runs(run_id, status, state_json, error) VALUES(?,?,?,?)",
            (record.run_id, record.status, json.dumps(record.state), record.error),
        )


def load_run(run_id: str) -> Optional[RunRecord]:
    conn = _conn()
    row = conn.execute("SELECT run_id, status, state_json, error FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not row:
        return None
    return RunRecord(run_id=row[0], status=row[1], state=json.loads(row[2]), error=row[3])
