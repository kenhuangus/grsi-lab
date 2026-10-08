"""SQLite-backed durable stores for sealed ledger and lineage."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class DurableStore:
    """Append-oriented SQLite store used by ledger and lineage."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sealed_decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              entry_hash TEXT NOT NULL UNIQUE,
              prev_hash TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lineage (
              lineage_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              opened_at TEXT NOT NULL,
              closed_at TEXT,
              close_reason TEXT,
              payload_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def append_sealed(self, entry: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO sealed_decisions(entry_hash, prev_hash, payload_json) VALUES (?,?,?)",
            (entry["entry_hash"], entry["prev_hash"], json.dumps(entry, sort_keys=True)),
        )
        self._conn.commit()

    def list_sealed(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT payload_json FROM sealed_decisions ORDER BY id ASC"
        ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def upsert_lineage(self, record: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO lineage(
              lineage_id, status, opened_at, closed_at, close_reason, payload_json
            )
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(lineage_id) DO UPDATE SET
              status=excluded.status,
              closed_at=excluded.closed_at,
              close_reason=excluded.close_reason,
              payload_json=excluded.payload_json
            """,
            (
                record["lineage_id"],
                record["status"],
                record["opened_at"],
                record.get("closed_at"),
                record.get("close_reason"),
                json.dumps(record, sort_keys=True),
            ),
        )
        self._conn.commit()

    def get_lineage(self, lineage_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload_json FROM lineage WHERE lineage_id=?",
            (lineage_id,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def close(self) -> None:
        self._conn.close()
