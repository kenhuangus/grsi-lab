"""Tests for signed promotion gateway."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lab04_isolation_eval.eval_service import SealedLedger
from lab05_promotion_ecosystem.frozen_policy import run_frozen_policy_scan
from lab05_promotion_ecosystem.promotion_gateway import PromotionError, promote
from rsi_core.crypto_tokens import mint_promotion_token

LINEAGE = "12345678-1234-4234-8234-123456789abc"

MANIFEST = {
    "version": "1.0",
    "components": [
        {
            "path": "adapters/x/",
            "owner": "lab",
            "eval_hook": "eval/score",
            "rollback_unit": "adapters.x",
            "observability_signal": "x_ok",
        }
    ],
    "locked": ["eval/", "held_out/", "ledger/", "CONTRACTS.md"],
}

CANDIDATE = {
    "lineage_id": LINEAGE,
    "surface": "model",
    "hypothesis": "Improve held-out accuracy",
    "metric": "held_out",
    "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
    "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
    "proposer_role": "implementer",
}


def _mint(scan_hash: str, **overrides: object) -> dict:
    token = mint_promotion_token(
        token_id="tok-1",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash=scan_hash,
    )
    token.update(overrides)
    return token


def test_promotion_without_token_fails() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    with pytest.raises(PromotionError, match="without token"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=None,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_promotion_with_signed_token_and_ledger() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = _mint(scan["report_hash"])
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=CANDIDATE,
        ledger=ledger,
    )
    assert result["status"] == "promoted"


def test_promotion_rejects_bad_signature() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = _mint(scan["report_hash"])
    token["signature"] = "AAAA" + token["signature"][4:]
    with pytest.raises(PromotionError):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_promotion_rejects_expired_token() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_promotion_token(
        token_id="tok-1",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        ttl_seconds=1,
    )
    # Force expiry in the past by reminting is hard; call with now far future after mint
    with pytest.raises(PromotionError, match="expired"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
            now=datetime(2099, 1, 1, tzinfo=UTC),
        )
