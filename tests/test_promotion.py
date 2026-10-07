"""Tests for promotion gateway token and sealed-decision requirements."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lab04_isolation_eval.eval_service import SealedLedger
from lab05_promotion_ecosystem.promotion_gateway import PromotionError, promote

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _token(**overrides: object) -> dict:
    base = {
        "token_id": "tok-1",
        "lineage_id": LINEAGE,
        "human_signer": "kenhuangus",
        "risk_tier": "low",
        "frozen_policy_scan_passed": True,
        "issued_at": "2026-10-06T12:00:00Z",
    }
    base.update(overrides)
    return base


def _keep_decision() -> dict:
    return {
        "lineage_id": LINEAGE,
        "decision": "keep",
        "score_authority": "external_evaluator",
        "metric_card_id": "card-1",
        "prev_hash": "GENESIS",
        "entry_hash": "a" * 64,
        "repro_script": "running_lab/repro_stub.py",
    }


def test_promotion_without_token_fails() -> None:
    with pytest.raises(PromotionError, match="without token"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=_keep_decision(),
            token=None,
        )


def test_promotion_with_valid_token() -> None:
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=_keep_decision(),
        token=_token(),
    )
    assert result["status"] == "promoted"
    assert result["token_id"] == "tok-1"
    assert result["entry_hash"] == "a" * 64


def test_promotion_rejects_non_keep() -> None:
    decision = _keep_decision()
    decision["decision"] = "revert"
    with pytest.raises(PromotionError, match="kept"):
        promote(lineage_id=LINEAGE, sealed_decision=decision, token=_token())


def test_promotion_rejects_invalid_sealed_decision() -> None:
    bad = _keep_decision()
    bad["entry_hash"] = "not-a-hash"
    with pytest.raises(PromotionError, match="invalid sealed decision"):
        promote(lineage_id=LINEAGE, sealed_decision=bad, token=_token())


def test_promotion_rejects_expired_token() -> None:
    token = _token(expires_at="2020-01-01T00:00:00Z")
    with pytest.raises(PromotionError, match="expired"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=_keep_decision(),
            token=token,
            now=datetime(2026, 10, 7, tzinfo=UTC),
        )


def test_promotion_with_ledger_tip() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro_stub.py",
        scores={"held_out": 0.9},
    )
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=_token(),
        ledger=ledger,
    )
    assert result["status"] == "promoted"
    assert result["entry_hash"] == sealed["entry_hash"]


def test_promotion_rejects_forged_tip_when_ledger_provided() -> None:
    ledger = SealedLedger()
    ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro_stub.py",
    )
    forged = _keep_decision()
    with pytest.raises(PromotionError, match="ledger tip"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=forged,
            token=_token(),
            ledger=ledger,
        )
