"""Promotion gateway — signed tokens, frozen-policy scan, ledger tip binding."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from jsonschema.exceptions import ValidationError

from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.pacing_hold import PacingHold, PacingHoldError
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import tier_allows_promote
from rsi_core.crypto_tokens import load_signing_key, verify_promotion_token
from rsi_core.schemas_load import validate_instance

if TYPE_CHECKING:
    from labs.ch08_measure.ledger import SealedLedger


class PromotionError(PermissionError):
    """Raised when promotion is attempted without a valid token."""


def validate_token(token: dict[str, Any], *, key: bytes | None = None) -> dict[str, Any]:
    """Schema + cryptographic validation of a promotion token."""
    return verify_promotion_token(token, key=key or load_signing_key())


def _parse_dt(value: str) -> datetime:
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
        raise PromotionError("promotion token missing expires_at")
    current = now or datetime.now(UTC)
    if _parse_dt(str(expires)) <= current:
        raise PromotionError("promotion token expired")


def promote(
    *,
    lineage_id: str,
    sealed_decision: dict[str, Any],
    token: dict[str, Any] | None,
    ownership_manifest: dict[str, Any],
    candidate: dict[str, Any],
    ledger: SealedLedger | None = None,
    now: datetime | None = None,
    key: bytes | None = None,
    pacing: PacingHold | None = None,
    kill_switch: Any | None = None,
    record_store: PromotionRecordStore | None = None,
) -> dict[str, Any]:
    """Promote a kept candidate only with a matching human-signed token.

    Requires:
    - optional kill switch clear
    - schema-valid sealed decision with decision=keep
    - HMAC-verified token matching lineage + scan report hash
    - fresh frozen-policy scan that passes and matches the token hash
    - when ledger provided: verified tip matching sealed decision
    - optional pacing hold release for medium/high/critical tiers
    - ``record_store`` to persist the promotion (required for success;
      Chapter 10 publish looks up the same store)
    """
    if kill_switch is not None:
        try:
            kill_switch.assert_alive()
        except RuntimeError as exc:
            raise PromotionError(str(exc)) from exc

    if token is None:
        raise PromotionError("promotion without token fails")

    try:
        decision = validate_instance("sealed_decision", sealed_decision)
    except ValidationError as exc:
        raise PromotionError(f"invalid sealed decision: {exc.message}") from exc

    try:
        validated = validate_token(token, key=key)
    except Exception as exc:
        raise PromotionError(str(exc)) from exc
    _assert_token_not_expired(validated, now=now)

    if decision.get("decision") != "keep":
        raise PromotionError("only kept candidates may be promoted")
    if validated["lineage_id"] != lineage_id:
        raise PromotionError("token lineage_id mismatch")
    if decision.get("lineage_id") != lineage_id:
        raise PromotionError("sealed decision lineage_id mismatch")

    # Token claim must match an actual scan result (not a hardcoded true).
    if validated.get("frozen_policy_scan_passed") is not True:
        raise PromotionError("token frozen_policy_scan_passed is not true")

    scan = run_frozen_policy_scan(
        candidate=candidate,
        ownership_manifest=ownership_manifest,
        sealed_decision=decision,
    )
    if not scan["passed"]:
        raise PromotionError(f"frozen policy scan failed: {scan['findings']}")
    if validated["frozen_policy_scan_report_hash"] != scan["report_hash"]:
        raise PromotionError("token scan report hash mismatch")

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

    risk_tier = str(validated["risk_tier"])
    if pacing is not None:
        pacing.record_attempt(lineage_id, risk_tier)
        try:
            pacing.assert_not_held(lineage_id)
        except PacingHoldError as exc:
            raise PromotionError(str(exc)) from exc
    elif not tier_allows_promote(risk_tier, pacing_released=False):
        # Without a pacing controller, medium+ tiers still refuse auto-promote.
        if risk_tier not in {"low"}:
            raise PromotionError(f"{risk_tier} tier requires pacing release")

    if record_store is None:
        raise PromotionError(
            "promotion requires record_store to persist the promotion record"
        )

    result = {
        "status": "promoted",
        "lineage_id": lineage_id,
        "token_id": validated["token_id"],
        "risk_tier": validated["risk_tier"],
        "human_signer": validated["human_signer"],
        "entry_hash": decision["entry_hash"],
        "scan_report_hash": scan["report_hash"],
        "frozen_policy_scan_passed": bool(scan["passed"]),
        "token": validated,
    }
    record_store.append(result)
    result["promotion_record_persisted"] = True
    return result
