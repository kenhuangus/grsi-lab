"""Hash-chained sealed decision ledger (memory + optional SQLite durability)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from rsi_core.durable_store import DurableStore
from rsi_core.schemas_load import validate_instance

GENESIS = "GENESIS"


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_entry(prev_hash: str, payload: dict[str, Any]) -> str:
    """Compute SHA-256 entry hash chained from ``prev_hash``."""
    material = prev_hash.encode("utf-8") + _canonical(payload)
    return hashlib.sha256(material).hexdigest()


@dataclass
class SealedLedger:
    """Hash-chained sealed decision ledger."""

    entries: list[dict[str, Any]] = field(default_factory=list)
    store: DurableStore | None = None

    def __post_init__(self) -> None:
        if self.store is not None and not self.entries:
            self.entries = self.store.list_sealed()

    @property
    def tip_hash(self) -> str:
        if not self.entries:
            return GENESIS
        return str(self.entries[-1]["entry_hash"])

    def seal(
        self,
        *,
        lineage_id: str,
        decision: str,
        metric_card_id: str,
        repro_script: str,
        scores: dict[str, float] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Append a schema-valid sealed_decision with hash chain linkage."""
        prev = self.tip_hash
        payload = {
            "lineage_id": lineage_id,
            "decision": decision,
            "score_authority": "external_evaluator",
            "metric_card_id": metric_card_id,
            "scores": scores or {},
            "repro_script": repro_script,
            "notes": notes or "",
        }
        entry_hash = hash_entry(prev, payload)
        sealed = {
            **payload,
            "prev_hash": prev,
            "entry_hash": entry_hash,
        }
        if not sealed["notes"]:
            del sealed["notes"]
        if not sealed["scores"]:
            del sealed["scores"]
        validated = validate_instance("sealed_decision", sealed)
        self.entries.append(validated)
        if self.store is not None:
            self.store.append_sealed(validated)
        return validated

    def verify_chain(self) -> bool:
        """Recompute hashes; return True if the chain is intact."""
        prev = GENESIS
        for entry in self.entries:
            payload = {
                k: entry[k]
                for k in (
                    "lineage_id",
                    "decision",
                    "score_authority",
                    "metric_card_id",
                    "scores",
                    "repro_script",
                    "notes",
                )
                if k in entry
            }
            if "scores" not in payload:
                payload["scores"] = {}
            if "notes" not in payload:
                payload["notes"] = ""
            expected = hash_entry(prev, payload)
            if entry.get("prev_hash") != prev or entry.get("entry_hash") != expected:
                return False
            prev = entry["entry_hash"]
        return True
