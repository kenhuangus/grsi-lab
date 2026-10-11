"""Lineage open/close helpers for Chapter 3 proposal envelopes."""

from __future__ import annotations

from typing import Any, Literal

from rsi_core.lineage import (
    LineageRecord,
    LineageStatus,
    close_lineage,
    get_lineage,
    open_lineage,
    reset_registry,
)
from rsi_core.types import parse_lineage_id

CloseDecision = Literal["keep", "revert", "reject"]


def open_proposal_lineage(
    *,
    role: str,
    surface: str | None = None,
    **metadata: Any,
) -> LineageRecord:
    """Open a lineage UUID at proposal time with role metadata."""
    meta = dict(metadata)
    meta["role"] = role
    if surface is not None:
        meta["surface"] = surface
    return open_lineage(**meta)


def assert_shared_lineage(planner: dict[str, Any], implementer: dict[str, Any]) -> str:
    """Require planner and implementer envelopes to share one lineage_id."""
    left = parse_lineage_id(str(planner["lineage_id"]))
    right = parse_lineage_id(str(implementer["lineage_id"]))
    if left != right:
        raise ValueError(
            f"lineage mismatch: planner={left} implementer={right}"
        )
    return left


def close_proposal_lineage(
    lineage_id: str,
    decision: CloseDecision,
    *,
    reason: str | None = None,
) -> LineageRecord:
    """Close a proposal lineage at keep/revert/reject (not promote)."""
    return close_lineage(lineage_id, decision, reason=reason)


def lineage_is_open(lineage_id: str) -> bool:
    """True if the lineage exists and is still OPEN."""
    record = get_lineage(lineage_id)
    return record.status is LineageStatus.OPEN


__all__ = [
    "LineageRecord",
    "LineageStatus",
    "assert_shared_lineage",
    "close_proposal_lineage",
    "get_lineage",
    "lineage_is_open",
    "open_proposal_lineage",
    "reset_registry",
]
