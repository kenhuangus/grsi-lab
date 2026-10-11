"""Chapter 9 promotion lab — accept + refuse paths."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from labs.ch08_measure.ledger import SealedLedger
from labs.ch09_promotion.evidence_pack import build_evidence_pack, verify_evidence_pack
from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.pacing_hold import PacingHold, PacingHoldError
from labs.ch09_promotion.promotion_gateway import PromotionError, promote
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token, tier_allows_promote
from labs.ch10_ecosystem.kill_rollback import KillSwitch

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


def _seal_keep(ledger: SealedLedger | None = None) -> tuple[SealedLedger, dict]:
    ledger = ledger or SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    return ledger, sealed


def _token_for(sealed: dict, candidate: dict = CANDIDATE, **overrides: object) -> dict:
    scan = run_frozen_policy_scan(
        candidate=candidate, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-1",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    token.update(overrides)
    return token


def test_promotion_without_token_fails() -> None:
    ledger, sealed = _seal_keep()
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
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
    store = PromotionRecordStore()
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=CANDIDATE,
        ledger=ledger,
        record_store=store,
    )
    assert result["status"] == "promoted"
    assert result["frozen_policy_scan_passed"] is True
    assert store.find_by_lineage(LINEAGE) is not None


def test_promotion_refuses_without_record_store() -> None:
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
    with pytest.raises(PromotionError, match="record_store"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_promote_refuses_when_sealed_decision_not_keep() -> None:
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="revert",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.1},
    )
    # Mint against a keep-shaped scan is impossible for promote; build token from
    # a synthetic keep seal hash path that still fails on decision != keep.
    keep_ledger, keep_sealed = _seal_keep()
    token = _token_for(keep_sealed)
    with pytest.raises(PromotionError, match="only kept"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_promote_refuses_tip_mismatch() -> None:
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
    # Advance ledger tip away from sealed decision
    ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-2",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.95},
    )
    with pytest.raises(PromotionError, match="ledger tip"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_promote_refuses_scan_hash_mismatch() -> None:
    ledger, sealed = _seal_keep()
    token = mint_risk_tier_token(
        token_id="tok-bad-hash",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash="ab" * 32,
        frozen_policy_scan_passed=True,
    )
    with pytest.raises(PromotionError, match="scan report hash"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
        )


def test_mint_refuses_failed_scan_flag() -> None:
    with pytest.raises(ValueError, match="frozen policy scan failed"):
        mint_risk_tier_token(
            token_id="tok-fail",
            lineage_id=LINEAGE,
            human_signer="kenhuangus",
            risk_tier="low",
            scan_report_hash="ab" * 32,
            frozen_policy_scan_passed=False,
        )


def test_promotion_persists_jsonl(tmp_path: Path) -> None:
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
    store = PromotionRecordStore(tmp_path)
    promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=CANDIDATE,
        ledger=ledger,
        record_store=store,
    )
    rows = store.list_records()
    assert len(rows) == 1
    assert rows[0]["status"] == "promoted"
    assert (tmp_path / "promotions.jsonl").is_file()


def test_kill_switch_blocks_promote() -> None:
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
    kill = KillSwitch()
    kill.kill("halt")
    with pytest.raises(PromotionError, match="kill switch"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
            kill_switch=kill,
        )


def test_promotion_rejects_bad_signature() -> None:
    ledger, sealed = _seal_keep()
    token = _token_for(sealed)
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
    ledger, sealed = _seal_keep()
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-1",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
        ttl_seconds=1,
    )
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


def test_frozen_scan_refuses_locked_path() -> None:
    bad = {**CANDIDATE, "diff": {"paths": ["eval/scorer.py"], "summary": "bad"}}
    _, sealed = _seal_keep()
    scan = run_frozen_policy_scan(
        candidate=bad, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    assert scan["passed"] is False


def test_evidence_pack_hash_roundtrip() -> None:
    _, sealed = _seal_keep()
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    pack = build_evidence_pack(
        sealed_decision=sealed, scan_report=scan, candidate=CANDIDATE
    )
    assert verify_evidence_pack(pack) is True
    pack["entry_hash"] = "0" * 64
    assert verify_evidence_pack(pack) is False


def test_pacing_hold_blocks_high_tier_until_release() -> None:
    assert tier_allows_promote("high", pacing_released=False) is False
    hold = PacingHold()
    hold.record_attempt(LINEAGE, "high")
    with pytest.raises(PacingHoldError):
        hold.assert_not_held(LINEAGE)
    hold.release(LINEAGE)
    hold.assert_not_held(LINEAGE)

    ledger, sealed = _seal_keep()
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-h",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="high",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    pacing = PacingHold()
    with pytest.raises(PromotionError, match="pacing hold"):
        promote(
            lineage_id=LINEAGE,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=CANDIDATE,
            ledger=ledger,
            pacing=pacing,
        )
    pacing.release(LINEAGE)
    pacing2 = PacingHold()
    pacing2.release(LINEAGE)
    result = promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=CANDIDATE,
        ledger=ledger,
        pacing=pacing2,
        record_store=PromotionRecordStore(),
    )
    assert result["status"] == "promoted"


def test_risk_tier_ttl_clamped() -> None:
    _, sealed = _seal_keep()
    scan = run_frozen_policy_scan(
        candidate=CANDIDATE, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-c",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="critical",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
        ttl_seconds=99_999,
    )
    issued = datetime.fromisoformat(token["issued_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(token["expires_at"].replace("Z", "+00:00"))
    assert (expires - issued).total_seconds() <= 900
