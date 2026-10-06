"""Lineage ID open/close helpers for RSI proposals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from rsi_core.types import LineageId, new_lineage_id, parse_lineage_id


class LineageStatus(str, Enum):
    OPEN = "open"
    KEEP = "keep"
    REVERT = "revert"
    REJECT = "reject"


@dataclass
class LineageRecord:
    """In-memory lineage opened at proposal time."""

    lineage_id: LineageId
    status: LineageStatus = LineageStatus.OPEN
    opened_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    closed_at: str | None = None
    close_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


_REGISTRY: dict[str, LineageRecord] = {}


def open_lineage(**metadata: Any) -> LineageRecord:
    """Open a new lineage UUID and register it as OPEN."""
    record = LineageRecord(lineage_id=new_lineage_id(), metadata=dict(metadata))
    _REGISTRY[record.lineage_id] = record
    return record


def get_lineage(lineage_id: str) -> LineageRecord:
    """Fetch a registered lineage or raise KeyError."""
    lid = parse_lineage_id(lineage_id)
    if lid not in _REGISTRY:
        raise KeyError(f"Unknown lineage_id: {lid}")
    return _REGISTRY[lid]


def close_lineage(
    lineage_id: str,
    decision: str,
    reason: str | None = None,
) -> LineageRecord:
    """Close a lineage at keep/revert/reject."""
    record = get_lineage(lineage_id)
    if record.status is not LineageStatus.OPEN:
        raise ValueError(f"Lineage already closed: {lineage_id} ({record.status})")
    try:
        status = LineageStatus(decision)
    except ValueError as exc:
        raise ValueError(
            f"decision must be keep|revert|reject, got {decision!r}"
        ) from exc
    if status is LineageStatus.OPEN:
        raise ValueError("Cannot close lineage as open")
    record.status = status
    record.closed_at = datetime.now(timezone.utc).isoformat()
    record.close_reason = reason
    return record


def reset_registry() -> None:
    """Clear in-memory lineage registry (tests / demo only)."""
    _REGISTRY.clear()
