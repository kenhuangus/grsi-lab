"""Experience admission gate with payload hashing and leak scanning."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

_LEAK_PATTERNS = (
    re.compile(r"held[_-]?out", re.I),
    re.compile(r"metric_card", re.I),
    re.compile(r"eval[_/]scorer", re.I),
    re.compile(r"BEGIN PRIVATE KEY"),
)


@dataclass
class AdmissionPolicy:
    """Policy for admitting experience into the training/replay buffer."""

    max_records: int = 1000
    require_lineage_id: bool = True
    require_quality: bool = True
    blocked_tags: set[str] = field(default_factory=lambda: {"exfil", "eval_leak"})
    min_quality: float = 0.0
    max_payload_bytes: int = 64_000


@dataclass
class AdmissionResult:
    admitted: bool
    reason: str
    record: dict[str, Any] | None = None


def _payload_bytes(payload: Any) -> bytes:
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload, sort_keys=True, default=str).encode("utf-8")


def admit_experience(
    record: dict[str, Any],
    policy: AdmissionPolicy,
    *,
    current_count: int = 0,
) -> AdmissionResult:
    """Admit or reject an experience record under ``policy``.

    Required: ``payload``. When ``require_lineage_id``: ``lineage_id``.
    When ``require_quality``: numeric ``quality`` (no defaulting to 1.0).
    """
    if current_count >= policy.max_records:
        return AdmissionResult(False, "buffer full", None)

    if policy.require_lineage_id and not record.get("lineage_id"):
        return AdmissionResult(False, "missing lineage_id", None)

    if "payload" not in record:
        return AdmissionResult(False, "missing payload", None)

    raw = _payload_bytes(record["payload"])
    if len(raw) > policy.max_payload_bytes:
        return AdmissionResult(False, "payload too large", None)

    text = raw.decode("utf-8", errors="replace")
    for pat in _LEAK_PATTERNS:
        if pat.search(text):
            return AdmissionResult(False, f"payload matched leak pattern: {pat.pattern}", None)

    tags = set(record.get("tags") or [])
    blocked = tags & policy.blocked_tags
    if blocked:
        return AdmissionResult(False, f"blocked tags: {sorted(blocked)}", None)

    if policy.require_quality:
        if "quality" not in record:
            return AdmissionResult(False, "missing quality", None)
        quality = float(record["quality"])
    else:
        quality = float(record.get("quality", 0.0))
    if quality < policy.min_quality:
        return AdmissionResult(False, "quality below threshold", None)

    admitted = dict(record)
    admitted["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    admitted["payload_bytes"] = len(raw)
    return AdmissionResult(True, "admitted", admitted)
