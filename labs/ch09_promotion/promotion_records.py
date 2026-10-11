"""Append-only promotion records (local JSONL; DurableStore-compatible payload)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rsi_core.durable_store import DurableStore


class PromotionRecordStore:
    """Persist successful promote results for Chapter 10 verification."""

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        durable: DurableStore | None = None,
    ) -> None:
        self.durable = durable
        self.root = Path(root) if root is not None else None
        self._memory: list[dict[str, Any]] = []
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self._jsonl = self.root / "promotions.jsonl"
        else:
            self._jsonl = None
        if self.durable is not None:
            self._ensure_durable_schema()

    def _ensure_durable_schema(self) -> None:
        assert self.durable is not None
        self.durable._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              lineage_id TEXT NOT NULL,
              token_id TEXT NOT NULL,
              entry_hash TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              recorded_at TEXT NOT NULL
            )
            """
        )
        self.durable._conn.commit()

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(record)
        payload.setdefault("recorded_at", datetime.now(UTC).isoformat())
        self._memory.append(payload)
        if self._jsonl is not None:
            with self._jsonl.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, sort_keys=True) + "\n")
        if self.durable is not None:
            self.durable._conn.execute(
                """
                INSERT INTO promotions(lineage_id, token_id, entry_hash, payload_json, recorded_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(payload.get("lineage_id") or ""),
                    str(payload.get("token_id") or ""),
                    str(payload.get("entry_hash") or ""),
                    json.dumps(payload, sort_keys=True),
                    str(payload["recorded_at"]),
                ),
            )
            self.durable._conn.commit()
        return payload

    def list_records(self) -> list[dict[str, Any]]:
        if self._jsonl is not None and self._jsonl.is_file():
            rows: list[dict[str, Any]] = []
            for line in self._jsonl.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
            return rows
        if self.durable is not None:
            cur = self.durable._conn.execute(
                "SELECT payload_json FROM promotions ORDER BY id ASC"
            )
            return [json.loads(r[0]) for r in cur.fetchall()]
        return list(self._memory)

    def find_by_lineage(self, lineage_id: str) -> dict[str, Any] | None:
        for row in reversed(self.list_records()):
            if row.get("lineage_id") == lineage_id:
                return row
        return None
