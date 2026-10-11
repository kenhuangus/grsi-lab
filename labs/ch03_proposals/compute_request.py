"""Compute-request envelopes for Chapter 3 — reject unscoped spends."""

from __future__ import annotations

from typing import Any, Literal

from rsi_core.compute_budget import ComputeBudgetError, ComputeBudgetLedger
from rsi_core.schemas_load import validate_instance
from rsi_core.types import parse_lineage_id

BudgetUnits = Literal["gpu_hours", "tokens", "wall_seconds", "dollars"]


def build_compute_request(
    *,
    lineage_id: str,
    units: BudgetUnits,
    amount: float,
    target_metric: str,
    stop_rule: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build and schema-validate a compute_request bound to a proposal lineage."""
    parse_lineage_id(lineage_id)
    if amount <= 0:
        raise ComputeBudgetError("unscoped compute: budget.amount must be > 0")
    if not target_metric.strip():
        raise ComputeBudgetError("unscoped compute: target_metric required")
    if not stop_rule.strip():
        raise ComputeBudgetError("unscoped compute: stop_rule required")
    request: dict[str, Any] = {
        "lineage_id": lineage_id,
        "budget": {"units": units, "amount": amount},
        "target_metric": target_metric,
        "stop_rule": stop_rule,
    }
    if notes is not None:
        request["notes"] = notes
    return validate_instance("compute_request", request)


def authorize_compute(
    request: dict[str, Any],
    *,
    amount: float,
    ledger: ComputeBudgetLedger,
    global_cap: float = 1_000_000.0,
) -> dict[str, Any]:
    """Authorize a spend against a shared ledger (fail closed over budget).

    A shared ``ledger`` is required. Silently constructing a fresh
    ``ComputeBudgetLedger`` would reset cumulative spend and hide over-budget
    refusals across calls — that path is refused.
    """
    if ledger is None:  # type: ignore[comparison-overlap]
        raise ComputeBudgetError(
            "shared ComputeBudgetLedger required; refusing silent fresh ledger "
            "that would reset cumulative spend"
        )
    return ledger.authorize_spend(request, amount=amount, global_cap=global_cap)


__all__ = [
    "ComputeBudgetError",
    "ComputeBudgetLedger",
    "authorize_compute",
    "build_compute_request",
]
