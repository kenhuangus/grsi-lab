"""Broker-owned experience store: quarantine → admit → append-only admitted store."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from labs.ch05_data_memory.admit_experience import (
    AdmissionPolicy,
    AdmissionResult,
    admit_experience,
)


@dataclass
class ExperienceBroker:
    """Only process path that may call ``admit_experience`` against production memory.

    Collectors write quarantine only. Rejected records stay in quarantine with
    an audit row; admitted records append under ``admitted/``.
    """

    root: Path
    policy: AdmissionPolicy = field(default_factory=AdmissionPolicy)
    _admitted: list[dict[str, Any]] = field(default_factory=list)
    _audit: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for name in ("quarantine", "admitted", "audit"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    @property
    def current_count(self) -> int:
        return len(self._admitted)

    def _owned_path(self, *parts: str) -> Path:
        """Resolve a store path that must remain under the broker root."""
        path = (self.root.joinpath(*parts)).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise PermissionError(f"store path escapes broker root: {path}")
        return path

    def quarantine_write(self, record: dict[str, Any]) -> Path:
        """Persist a collector record under quarantine (not indexed for retrieval)."""
        payload = record.get("payload")
        raw = (
            payload
            if isinstance(payload, (bytes, bytearray))
            else json.dumps(record, sort_keys=True, default=str).encode("utf-8")
        )
        digest = hashlib.sha256(raw).hexdigest()[:16]
        path = self._owned_path("quarantine", f"{digest}.json")
        path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        return path

    def admit_from_quarantine(self, record: dict[str, Any]) -> AdmissionResult:
        """Run admission; append to admitted store or leave in quarantine with audit."""
        result = admit_experience(
            record,
            self.policy,
            current_count=self.current_count,
        )
        stamp = datetime.now(UTC).isoformat()
        if result.admitted and result.record is not None:
            admitted = dict(result.record)
            admitted["admitted_at"] = stamp
            self._admitted.append(admitted)
            digest = admitted["payload_sha256"][:16]
            out = self._owned_path("admitted", f"{digest}.json")
            out.write_text(json.dumps(admitted, indent=2, default=str), encoding="utf-8")
            self._audit.append(
                {"event": "admit", "at": stamp, "reason": result.reason, "digest": digest}
            )
        else:
            digest = hashlib.sha256(
                json.dumps(record, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
            audit_row = {
                "event": "reject",
                "at": stamp,
                "reason": result.reason,
                "digest": digest,
                "record_keys": sorted(record.keys()),
            }
            self._audit.append(audit_row)
            audit_path = self._owned_path("audit", f"{digest}.json")
            audit_path.write_text(json.dumps(audit_row, indent=2), encoding="utf-8")
        return result

    def list_admitted(self) -> list[dict[str, Any]]:
        return list(self._admitted)

    def list_audit(self) -> list[dict[str, Any]]:
        return list(self._audit)
