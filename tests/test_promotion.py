"""Tests for promotion gateway token requirement."""

from __future__ import annotations

import pytest

from lab05_promotion_ecosystem.promotion_gateway import PromotionError, promote


LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _keep_decision() -> dict:
    return {
        "lineage_id": LINEAGE,
        "decision": "keep",
        "score_authority": "external_evaluator",
        "metric_card_id": "card-1",
        "prev_hash": "GENESIS",
        "entry_hash": "a" * 64,
        "repro_script": "scripts/repro.py",
    }


def test_promotion_without_token_fails() -> None:
    with pytest.raises(PromotionError, match="without token"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=_keep_decision(),
            token=None,
        )


def test_promotion_with_valid_token() -> None:
    token = {
        "token_id": "tok-1",
        "lineage_id": LINEAGE,
        "human_signer": "kenhuangus",
        "risk_tier": "low",
        "frozen_policy_scan_passed": True,
        "issued_at": "2026-10-06T12:00:00Z",
    }
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=_keep_decision(),
        token=token,
    )
    assert result["status"] == "promoted"
    assert result["token_id"] == "tok-1"


def test_promotion_rejects_non_keep() -> None:
    token = {
        "token_id": "tok-1",
        "lineage_id": LINEAGE,
        "human_signer": "kenhuangus",
        "risk_tier": "medium",
        "frozen_policy_scan_passed": True,
        "issued_at": "2026-10-06T12:00:00Z",
    }
    decision = _keep_decision()
    decision["decision"] = "revert"
    with pytest.raises(PromotionError, match="kept"):
        promote(lineage_id=LINEAGE, sealed_decision=decision, token=token)
