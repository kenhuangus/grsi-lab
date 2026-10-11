"""Experience admission gate with payload hashing, leak scanning, and collapse guards."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from rsi_core.types import parse_lineage_id

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
    min_entropy: float = 2.5
    require_module_id: bool = False


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


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def admit_experience(
    record: dict[str, Any],
    policy: AdmissionPolicy,
    *,
    current_count: int = 0,
) -> AdmissionResult:
    """Admit or reject an experience record under ``policy``.

    Required: ``payload``. When ``require_lineage_id``: UUID ``lineage_id``
    via ``parse_lineage_id``. When ``require_quality``: numeric ``quality``
    (no defaulting to 1.0).
    """
    if current_count >= policy.max_records:
        return AdmissionResult(False, "buffer full", None)

    if policy.require_lineage_id:
        raw_lineage = record.get("lineage_id")
        if not raw_lineage:
            return AdmissionResult(False, "missing lineage_id", None)
        try:
            lineage_id = parse_lineage_id(str(raw_lineage))
        except ValueError:
            return AdmissionResult(False, f"invalid lineage_id: {raw_lineage!r}", None)
    else:
        lineage_id = None
        if record.get("lineage_id") is not None:
            try:
                lineage_id = parse_lineage_id(str(record["lineage_id"]))
            except ValueError:
                return AdmissionResult(
                    False, f"invalid lineage_id: {record['lineage_id']!r}", None
                )

    if "payload" not in record:
        return AdmissionResult(False, "missing payload", None)

    if policy.require_module_id and not record.get("module_id"):
        return AdmissionResult(False, "missing module_id", None)

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

    entropy = _shannon_entropy(text)
    if entropy < policy.min_entropy:
        return AdmissionResult(False, "entropy below collapse floor", None)

    admitted = dict(record)
    if lineage_id is not None:
        admitted["lineage_id"] = lineage_id
    admitted["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    admitted["payload_bytes"] = len(raw)
    admitted["payload_entropy"] = entropy
    return AdmissionResult(True, "admitted", admitted)


def verify_experience_admission(
    record: dict[str, Any],
    policy: AdmissionPolicy,
    *,
    current_count: int = 0,
    min_entropy: float | None = None,
) -> AdmissionResult:
    """Admission with an optional override for the collapse entropy floor."""
    if min_entropy is not None:
        policy = AdmissionPolicy(
            max_records=policy.max_records,
            require_lineage_id=policy.require_lineage_id,
            require_quality=policy.require_quality,
            blocked_tags=set(policy.blocked_tags),
            min_quality=policy.min_quality,
            max_payload_bytes=policy.max_payload_bytes,
            min_entropy=min_entropy,
            require_module_id=policy.require_module_id,
        )
    return admit_experience(record, policy, current_count=current_count)
