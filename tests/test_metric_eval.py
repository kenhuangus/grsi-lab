"""Metric-card evaluation over real fixture datasets."""

from __future__ import annotations

from pathlib import Path

from lab04_isolation_eval.eval_service import SealedLedger, adversary_pass, evaluate_keep
from lab04_isolation_eval.metric_eval import evaluate_metric_card, load_metric_card

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = "12345678-1234-4234-8234-123456789abc"


def test_metric_card_scores_from_fixtures() -> None:
    card = load_metric_card(ROOT / "fixtures/metric_cards/lab_metric_card.json")
    bundle = evaluate_metric_card(
        card,
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
        tokens_used=1000,
    )
    assert bundle.scores["held_out"] == 1.0
    assert bundle.ablation_ok is True


def test_adversary_pass_blocks_eval_paths() -> None:
    cand = {
        "lineage_id": LINEAGE,
        "surface": "model",
        "hypothesis": "rewrite evaluator secretly",
        "metric": "held_out",
        "rollback": {"unit": "x", "snapshot_ref": "snap://x"},
        "diff": {"paths": ["eval/scorer.py"], "summary": "bad"},
        "proposer_role": "implementer",
    }
    finding = adversary_pass(cand)
    assert finding.passed is False


def test_evaluate_keep_measures_not_injects() -> None:
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
    sealed = evaluate_keep(
        cand,
        ledger,
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        keep_threshold=0.5,
        tokens_used=1000,
        ablation_module_scores={"adapter": 0.0},
    )
    assert sealed["decision"] == "keep"
    assert sealed["scores"]["held_out"] == 1.0
    assert ledger.verify_chain()
