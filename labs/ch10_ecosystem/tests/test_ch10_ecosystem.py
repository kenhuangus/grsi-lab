"""Chapter 10 ecosystem lab — accept + refuse paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from labs.ch06_orchestration.harness_store import HarnessStore
from labs.ch07_isolation.receipts import issue_receipt
from labs.ch07_isolation.sandbox_profile import default_lab_profile
from labs.ch08_measure.evaluate_keep import evaluate_keep
from labs.ch08_measure.ledger import SealedLedger
from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.promotion_gateway import promote
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token
from labs.ch10_ecosystem.boundary_proxy import BoundaryProxy, EgressDenied
from labs.ch10_ecosystem.dry_run import run_ecosystem_dry_run
from labs.ch10_ecosystem.failure_atlas import by_loop_step, index_by_step, load_entries
from labs.ch10_ecosystem.kill_rollback import KillSwitch, kill_and_rollback
from labs.ch10_ecosystem.publication_gate import PublicationError, PublicationGate

LINEAGE = "12345678-1234-4234-8234-123456789abc"
ROOT = Path(__file__).resolve().parents[3]

PROFILE = {
    "profile_id": "lab-eco-profile",
    "filesystem_jail": True,
    "egress_allow": ["example.com"],
    "blocked_paths": ["eval/"],
    "widening_allowed": False,
}

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


def _real_promote() -> tuple[dict[str, Any], PromotionRecordStore]:
    cand = {
        "lineage_id": LINEAGE,
        "surface": "model",
        "hypothesis": "Improve held-out accuracy",
        "metric": "held_out",
        "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
        "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
        "proposer_role": "implementer",
    }
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="lab-metric-card",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    scan = run_frozen_policy_scan(
        candidate=cand, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-ch10",
        lineage_id=LINEAGE,
        human_signer="kenhuangus",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    store = PromotionRecordStore()
    promoted = promote(
        lineage_id=LINEAGE,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=cand,
        ledger=ledger,
        record_store=store,
    )
    return promoted, store


def test_egress_denied_for_unknown_host() -> None:
    proxy = BoundaryProxy(sandbox_profile=PROFILE, allowed_hosts={"example.com"})
    with pytest.raises(EgressDenied):
        proxy.request("evil.example", lineage_id=LINEAGE, purpose="x")


def test_egress_allowed_without_network() -> None:
    proxy = BoundaryProxy(sandbox_profile=PROFILE, allowed_hosts={"example.com"})
    entry = proxy.request("example.com", lineage_id=LINEAGE, purpose="ok")
    assert entry["status"] == "allowed"
    assert len(proxy.log) == 1


def test_delegation_requires_gates() -> None:
    proxy = BoundaryProxy(sandbox_profile=PROFILE, allowed_hosts={"example.com"})
    with pytest.raises(EgressDenied, match="evaluation_gates"):
        proxy.open_delegation_channel(
            channel_id="c1",
            delegator_lineage_id=LINEAGE,
            specialist_role="retriever",
            evaluation_gates=[],
        )


def test_failure_atlas_by_step() -> None:
    entries = load_entries()
    promote_rows = by_loop_step(entries, "promote")
    assert promote_rows
    indexed = index_by_step(entries)
    assert "promote" in indexed
    with pytest.raises(ValueError):
        by_loop_step(entries, "not-a-step")


def test_publication_refuses_without_promote() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    with pytest.raises(PublicationError, match="without promotion"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result=None,
            lineage_id=LINEAGE,
            record_store=PromotionRecordStore(),
        )


def test_publication_refuses_forged_promoted_dict() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    with pytest.raises(PublicationError, match="persisted promotion record"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result={
                "status": "promoted",
                "lineage_id": LINEAGE,
                "token_id": "t",
                "entry_hash": "a" * 64,
            },
            lineage_id=LINEAGE,
            record_store=PromotionRecordStore(),
        )


def test_publication_refuses_persisted_claim_without_token() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    with pytest.raises(PublicationError, match="no persisted promotion record"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result={
                "status": "promoted",
                "lineage_id": LINEAGE,
                "token_id": "t",
                "entry_hash": "a" * 64,
                "promotion_record_persisted": True,
            },
            lineage_id=LINEAGE,
            record_store=PromotionRecordStore(),
        )


def test_publication_refuses_hmac_token_without_store_record() -> None:
    """Valid lab HMAC token + persisted flag is not enough without store lookup."""
    gate = PublicationGate(partner_allowlist={"partner-a"})
    token = mint_risk_tier_token(
        token_id="tok-forge",
        lineage_id=LINEAGE,
        human_signer="forger",
        risk_tier="low",
        scan_report_hash="ab" * 32,
        frozen_policy_scan_passed=True,
    )
    with pytest.raises(PublicationError, match="no persisted promotion record"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result={
                "status": "promoted",
                "lineage_id": LINEAGE,
                "token_id": token["token_id"],
                "entry_hash": "a" * 64,
                "promotion_record_persisted": True,
                "token": token,
            },
            lineage_id=LINEAGE,
            record_store=PromotionRecordStore(),
        )


def test_publication_refuses_without_record_store() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    promoted, _ = _real_promote()
    with pytest.raises(PublicationError, match="PromotionRecordStore"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result=promoted,
            lineage_id=LINEAGE,
        )


def test_publication_refuses_unknown_partner() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    promoted, store = _real_promote()
    with pytest.raises(PublicationError, match="not allowlisted"):
        gate.publish(
            artifact_id="a1",
            partner="partner-z",
            promotion_result=promoted,
            lineage_id=LINEAGE,
            record_store=store,
        )


def test_publication_accept_with_verified_promote() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"})
    promoted, store = _real_promote()
    result = gate.publish(
        artifact_id="a1",
        partner="partner-a",
        promotion_result=promoted,
        lineage_id=LINEAGE,
        record_store=store,
    )
    assert result["status"] == "published"
    assert result["token_id"] == promoted["token_id"]


def test_kill_and_rollback_restores_modules() -> None:
    harness = HarnessStore(modules={"planner": {"lr": 0.1}})
    harness.mutate("planner", {"lr": 0.9})
    kill = KillSwitch()
    result = kill_and_rollback(kill, harness, reason="test")
    assert result["status"] == "rolled_back"
    assert kill.engaged is True
    assert harness.modules["planner"]["lr"] == 0.1
    with pytest.raises(RuntimeError, match="kill switch engaged"):
        kill.assert_alive()


def test_publication_blocked_when_kill_engaged() -> None:
    gate = PublicationGate(partner_allowlist={"partner-a"}, kill_engaged=True)
    promoted, store = _real_promote()
    with pytest.raises(PublicationError, match="kill switch"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result=promoted,
            lineage_id=LINEAGE,
            record_store=store,
        )


def test_kill_switch_blocks_publish_via_assert_alive() -> None:
    kill = KillSwitch()
    kill.kill("halt publish")
    gate = PublicationGate(partner_allowlist={"partner-a"}, kill_switch=kill)
    promoted, store = _real_promote()
    with pytest.raises(PublicationError, match="kill switch"):
        gate.publish(
            artifact_id="a1",
            partner="partner-a",
            promotion_result=promoted,
            lineage_id=LINEAGE,
            record_store=store,
        )


def test_kill_blocks_evaluate_keep() -> None:
    kill = KillSwitch()
    kill.kill("halt eval")
    receipt = issue_receipt(
        lineage_id=LINEAGE,
        profile=default_lab_profile(),
        diff_paths=["adapters/x/"],
        clean=True,
    ).to_dict()
    sealed = evaluate_keep(
        {
            "lineage_id": LINEAGE,
            "surface": "model",
            "hypothesis": "Improve held-out accuracy",
            "metric": "held_out",
            "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
            "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
            "proposer_role": "implementer",
            "isolation_receipt": receipt,
        },
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
        kill_switch=kill,
    )
    assert sealed["decision"] == "reject"
    assert "kill switch" in (sealed.get("notes") or "")


def test_ecosystem_dry_run_all_ok() -> None:
    summary = run_ecosystem_dry_run()
    assert summary["all_ok"] is True
