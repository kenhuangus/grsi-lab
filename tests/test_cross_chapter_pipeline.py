"""Cross-chapter integration: ownership → propose → isolate → keep → promote → publish.

Fail-closed at each gate. Uses tempdirs / fixtures only (no network).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from labs.ch03_proposals.lineage import (
    close_proposal_lineage,
    open_proposal_lineage,
    reset_registry,
)
from labs.ch03_proposals.reject_gates import build_proposal
from labs.ch04_model_surface.cheapest_surface import CheaperAttempt, require_cheapest_surface
from labs.ch06_orchestration.bi_level_loop import BiLevelLoop, make_fixture_scorer
from labs.ch06_orchestration.harness_store import HarnessStore
from labs.ch07_isolation.receipts import ReceiptStore
from labs.ch07_isolation.run_isolated import run_isolated
from labs.ch08_measure.evaluate_keep import evaluate_keep
from labs.ch08_measure.ledger import SealedLedger
from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.promotion_gateway import PromotionError, promote
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token
from labs.ch10_ecosystem.publication_gate import PublicationError, PublicationGate
from rsi_core.types import LockedPathError, Surface

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = {
    "version": "1.0",
    "components": [
        {
            "path": "harness/planner.py",
            "owner": "lab",
            "eval_hook": "eval/held_out_score",
            "rollback_unit": "harness.planner",
            "observability_signal": "planner_latency_ms",
            "surface": "orchestration",
        },
        {
            "path": "adapters/",
            "owner": "ml",
            "eval_hook": "eval/held_out_score",
            "rollback_unit": "adapters.candidate_v1",
            "observability_signal": "held_out_accuracy",
            "surface": "model",
        },
    ],
    "locked": [
        "eval/",
        "evaluators/",
        "held_out/",
        "metric_cards/",
        "ledger/",
        "schemas/",
        "fixtures/datasets/",
        "fixtures/metric_cards/",
        "CONTRACTS.md",
        "ownership/",
        "safety/",
        "sandbox/",
        "promotion/",
    ],
}


@pytest.fixture(autouse=True)
def _clean_lineage() -> None:
    reset_registry()
    yield
    reset_registry()


def test_cross_chapter_pipeline_keep_promote_publish(tmp_path: Path) -> None:
    """Happy path through Ch3→Ch4→Ch6→Ch7→Ch8→Ch9→Ch10 with fail-closed gates."""
    metric = "held_out_accuracy"

    # Ch3: cheaper orchestration lineage opened then closed (evidence for Ch4).
    cheaper = open_proposal_lineage(
        role="implementer", surface="orchestration", metric=metric
    )
    orch_proposal = build_proposal(
        surface=Surface.ORCHESTRATION,
        hypothesis="Harness prompt edit lifts held_out_accuracy",
        metric=metric,
        paths=["harness/planner.py"],
        summary="planner prompt tweak",
        rollback_unit="harness.planner",
        snapshot_ref="snap://harness.planner@0",
        proposer_role="implementer",
        ownership_manifest=MANIFEST,
        lineage_id=cheaper.lineage_id,
    )
    assert orch_proposal["lineage_id"] == cheaper.lineage_id
    close_proposal_lineage(cheaper.lineage_id, "revert", reason="failed_min_delta")

    # Ch4: model open only after registered closed cheaper lineage.
    escalation = require_cheapest_surface(
        metric=metric,
        failure_statement="held_out_accuracy below card threshold after harness try",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id=cheaper.lineage_id,
                surface="orchestration",
                metric=metric,
                outcome="failed_min_delta",
            )
        ],
        harness_candidates=["harness/planner.py"],
    )
    assert escalation.allowed is True

    # Ch3: model proposal with declared adapters path + same ownership manifest.
    model_proposal = build_proposal(
        surface=Surface.MODEL,
        hypothesis=(
            f"{escalation.message}; adapter improves held_out_accuracy "
            "without touching eval surfaces"
        ),
        metric=metric,
        paths=["adapters/candidate_v1/"],
        summary="on-disk adapter candidate",
        rollback_unit="adapters.candidate_v1",
        snapshot_ref="snap://adapters/candidate_v1@0",
        proposer_role="implementer",
        ownership_manifest=MANIFEST,
    )

    # Ch6: optional harness keep with external fixture scorer (not self-score).
    store = HarnessStore(
        modules={"planner": {"prompt": "base"}},
        backbone_pin="bb-pipeline",
        require_registered_schema=True,
    )
    fixtures = {"base": 0.50, "improved planner": 0.62}
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        noise_floor=0.01,
        max_policy_tokens=64,
    )
    harness_keep = loop.propose_and_evaluate(
        "planner",
        {"prompt": "improved planner"},
        tool_schema={"name": "search", "parameters": {"q": {"type": "string"}}},
        backbone_pin="bb-pipeline",
    )
    assert harness_keep.kept is True

    # Ch7: isolation receipt via runner (HMAC), not forged clean:true.
    receipt_store = ReceiptStore(tmp_path / "receipts")
    isolated = run_isolated(
        {
            **model_proposal,
            "paths": list(model_proposal["diff"]["paths"]),
            "tenant_id": "lab",
        },
        receipt_store=receipt_store,
    )
    assert isolated.ok is True
    assert isolated.receipt is not None
    assert isolated.receipt.clean is True
    model_proposal["isolation_receipt"] = isolated.receipt.to_dict()

    # Ch8: evaluate_keep → keep (external metric card + verified receipt store).
    ledger = SealedLedger()
    sealed = evaluate_keep(
        model_proposal,
        ledger,
        metric_card_path=ROOT / "fixtures" / "metric_cards" / "lab_metric_card.json",
        dataset_root=ROOT / "fixtures" / "datasets",
        keep_threshold=0.5,
        tokens_used=1000.0,
        ablation_module_scores={"adapter": 0.0},
        receipt_store=receipt_store,
    )
    assert sealed["decision"] == "keep"
    assert ledger.verify_chain() is True

    # Ch9: refuse non-keep / no-token, then mint+promote with persisted record.
    with pytest.raises(PromotionError, match="without token"):
        promote(
            lineage_id=model_proposal["lineage_id"],
            sealed_decision=sealed,
            token=None,
            ownership_manifest=MANIFEST,
            candidate=model_proposal,
            ledger=ledger,
        )

    scan = run_frozen_policy_scan(
        candidate=model_proposal,
        ownership_manifest=MANIFEST,
        sealed_decision=sealed,
    )
    assert scan["passed"] is True
    token = mint_risk_tier_token(
        token_id="tok-cross-1",
        lineage_id=model_proposal["lineage_id"],
        human_signer="lab-operator",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    record_store = PromotionRecordStore(tmp_path / "promotions")
    promoted = promote(
        lineage_id=model_proposal["lineage_id"],
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=model_proposal,
        ledger=ledger,
        record_store=record_store,
    )
    assert promoted["status"] == "promoted"
    assert promoted["promotion_record_persisted"] is True
    assert record_store.find_by_lineage(model_proposal["lineage_id"]) is not None

    # Ch10: publish only with verified promote token + store-backed record.
    gate = PublicationGate(partner_allowlist={"lab-partner"})
    with pytest.raises(PublicationError, match="without promotion"):
        gate.publish(
            artifact_id="adapters/candidate_v1",
            partner="lab-partner",
            promotion_result=None,
            lineage_id=model_proposal["lineage_id"],
            record_store=record_store,
        )
    published = gate.publish(
        artifact_id="adapters/candidate_v1",
        partner="lab-partner",
        promotion_result=promoted,
        lineage_id=model_proposal["lineage_id"],
        record_store=record_store,
    )
    assert published["status"] == "published"
    assert published["token_id"] == promoted["token_id"]


def test_cross_chapter_refuses_locked_path_proposal() -> None:
    """Ch3 fail-closed: locked eval path cannot open a proposal."""
    with pytest.raises(LockedPathError):
        build_proposal(
            surface=Surface.MODEL,
            hypothesis="touch evaluator",
            metric="held_out_accuracy",
            paths=["eval/scorer.py"],
            summary="bad",
            rollback_unit="eval.scorer",
            snapshot_ref="snap://eval",
            proposer_role="implementer",
            ownership_manifest=MANIFEST,
        )


def test_cross_chapter_refuses_cheapest_without_closed_lineage() -> None:
    """Ch4 fail-closed: self-attested cheaper lineage is refused."""
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id="12345678-1234-4234-8234-123456789abc",
                surface="orchestration",
                metric="held_out_accuracy",
                outcome="failed_min_delta",
            )
        ],
        harness_candidates=["harness/planner.py"],
    )
    assert decision.allowed is False
    assert any("not in registry" in r for r in decision.refusals)
