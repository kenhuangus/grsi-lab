"""Promotion gateway — sandbox keep does not unlock production."""

from __future__ import annotations

from typing import Any

from rsi_core.schemas_load import validate_instance


class PromotionError(PermissionError):
    """Raised when promotion is attempted without a valid token."""


def validate_token(token: dict[str, Any]) -> dict[str, Any]:
    """Schema-validate a promotion token."""
    return validate_instance("promotion_token", token)


def promote(
    *,
    lineage_id: str,
    sealed_decision: dict[str, Any],
    token: dict[str, Any] | None,
) -> dict[str, Any]:
    """Promote a kept candidate only with a matching human-signed token.

    Rules
    -----
    - ``sealed_decision.decision`` must be ``keep``
    - ``token`` must validate and match ``lineage_id``
    - ``frozen_policy_scan_passed`` must be true (enforced by schema)
    """
    if token is None:
        raise PromotionError("promotion without token fails")

    validated = validate_token(token)
    if sealed_decision.get("decision") != "keep":
        raise PromotionError("only kept candidates may be promoted")
    if validated["lineage_id"] != lineage_id:
        raise PromotionError("token lineage_id mismatch")
    if sealed_decision.get("lineage_id") != lineage_id:
        raise PromotionError("sealed decision lineage_id mismatch")

    return {
        "status": "promoted",
        "lineage_id": lineage_id,
        "token_id": validated["token_id"],
        "risk_tier": validated["risk_tier"],
        "human_signer": validated["human_signer"],
    }
