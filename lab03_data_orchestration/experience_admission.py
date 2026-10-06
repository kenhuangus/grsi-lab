"""Experience admission gate for the data surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdmissionPolicy:
    """Policy for admitting experience into the training/replay buffer."""

    max_records: int = 1000
    require_lineage_id: bool = True
    blocked_tags: set[str] = field(default_factory=lambda: {"exfil", "eval_leak"})
    min_quality: float = 0.0


@dataclass
class AdmissionResult:
    admitted: bool
    reason: str
    record: dict[str, Any] | None = None


def admit_experience(
    record: dict[str, Any],
    policy: AdmissionPolicy,
    *,
    current_count: int = 0,
) -> AdmissionResult:
    """Admit or reject an experience record under ``policy``.

    Required fields when ``require_lineage_id``: ``lineage_id``, ``payload``.
    Optional: ``tags`` (list[str]), ``quality`` (float).
    """
    if current_count >= policy.max_records:
        return AdmissionResult(False, "buffer full", None)

    if policy.require_lineage_id and not record.get("lineage_id"):
        return AdmissionResult(False, "missing lineage_id", None)

    if "payload" not in record:
        return AdmissionResult(False, "missing payload", None)

    tags = set(record.get("tags") or [])
    blocked = tags & policy.blocked_tags
    if blocked:
        return AdmissionResult(False, f"blocked tags: {sorted(blocked)}", None)

    quality = float(record.get("quality", 1.0))
    if quality < policy.min_quality:
        return AdmissionResult(False, "quality below threshold", None)

    return AdmissionResult(True, "admitted", dict(record))
