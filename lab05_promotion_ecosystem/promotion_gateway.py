"""Promotion gateway — sandbox keep does not unlock production."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from jsonschema.exceptions import ValidationError

from rsi_core.schemas_load import validate_instance

if TYPE_CHECKING:
    from lab04_isolation_eval.eval_service import SealedLedger


class PromotionError(PermissionError):
    """Raised when promotion is attempted without a valid token."""


def validate_token(token: dict[str, Any]) -> dict[str, Any]:
    """Schema-validate a promotion token."""
    return validate_instance("promotion_token", token)


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 timestamp (accept trailing Z)."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _assert_token_not_expired(token: dict[str, Any], *, now: datetime | None = None) -> None:
    expires = token.get("expires_at")
    if not expires:
        return
    current = now or datetime.now(UTC)
    if _parse_dt(str(expires)) <= current:
        raise PromotionError("promotion token expired")


def promote(
    *,
    lineage_id: str,
    sealed_decision: dict[str, Any],
    token: dict[str, Any] | None,
    ledger: SealedLedger | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Promote a kept candidate only with a matching human-signed token.

    Rules
    -----
    - ``sealed_decision`` must schema-validate as ``sealed_decision``
    - ``sealed_decision.decision`` must be ``keep``
    - ``token`` must validate, match ``lineage_id``, and not be expired
    - ``frozen_policy_scan_passed`` must be true (enforced by schema)
    - When ``ledger`` is provided, the chain must verify and the tip entry
      must match ``sealed_decision`` (entry_hash + lineage_id + decision)
    """
    if token is None:
        raise PromotionError("promotion without token fails")

    try:
        decision = validate_instance("sealed_decision", sealed_decision)
    except ValidationError as exc:
        raise PromotionError(f"invalid sealed decision: {exc.message}") from exc

    validated = validate_token(token)
    _assert_token_not_expired(validated, now=now)

    if decision.get("decision") != "keep":
        raise PromotionError("only kept candidates may be promoted")
    if validated["lineage_id"] != lineage_id:
        raise PromotionError("token lineage_id mismatch")
    if decision.get("lineage_id") != lineage_id:
        raise PromotionError("sealed decision lineage_id mismatch")

    if ledger is not None:
        if not ledger.verify_chain():
            raise PromotionError("sealed ledger chain verification failed")
        if not ledger.entries:
            raise PromotionError("sealed ledger is empty")
        tip = ledger.entries[-1]
        if tip.get("entry_hash") != decision.get("entry_hash"):
            raise PromotionError("sealed decision is not the ledger tip")
        if tip.get("lineage_id") != lineage_id or tip.get("decision") != "keep":
            raise PromotionError("ledger tip is not a keep for this lineage")

    return {
        "status": "promoted",
        "lineage_id": lineage_id,
        "token_id": validated["token_id"],
        "risk_tier": validated["risk_tier"],
        "human_signer": validated["human_signer"],
        "entry_hash": decision["entry_hash"],
    }
