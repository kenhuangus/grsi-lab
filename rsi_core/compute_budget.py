"""Compute-request validation and in-process budget ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rsi_core.schemas_load import validate_instance


class ComputeBudgetError(PermissionError):
    """Raised when a compute request is unscoped or over budget."""


@dataclass
class ComputeBudgetLedger:
    """Tracks cumulative compute spends keyed by lineage_id and units."""

    spent: dict[tuple[str, str], float] = field(default_factory=dict)

    def validate_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Validate schema and reject unscoped requests."""
        validated = validate_instance("compute_request", request)
        budget = validated["budget"]
        if float(budget["amount"]) <= 0:
            raise ComputeBudgetError("unscoped compute: budget.amount must be > 0")
        if not validated.get("stop_rule"):
            raise ComputeBudgetError("unscoped compute: stop_rule required")
        if not validated.get("target_metric"):
            raise ComputeBudgetError("unscoped compute: target_metric required")
        return validated

    def authorize_spend(
        self,
        request: dict[str, Any],
        *,
        amount: float,
        global_cap: float = 1_000_000.0,
    ) -> dict[str, Any]:
        """Authorize a spend against the request budget and a global lineage cap."""
        validated = self.validate_request(request)
        lineage = validated["lineage_id"]
        units = validated["budget"]["units"]
        max_amount = float(validated["budget"]["amount"])
        if amount <= 0 or amount > max_amount:
            raise ComputeBudgetError(
                f"spend amount={amount} outside request budget {max_amount} {units}"
            )
        key = (lineage, units)
        prior = self.spent.get(key, 0.0) + amount
        if prior > global_cap:
            raise ComputeBudgetError(f"lineage {units} cap exceeded")
        self.spent[key] = prior
        return {
            "status": "authorized",
            "lineage_id": lineage,
            "units": units,
            "amount": amount,
            "spent": prior,
        }
