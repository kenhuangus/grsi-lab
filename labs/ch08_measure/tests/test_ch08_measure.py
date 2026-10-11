"""Chapter 8 measure lab — accept + refuse paths."""

from __future__ import annotations

from pathlib import Path

from labs.ch07_isolation.receipts import issue_receipt
from labs.ch07_isolation.sandbox_profile import default_lab_profile
from labs.ch08_measure.adversary_pass import adversary_pass
from labs.ch08_measure.evaluate_keep import evaluate_keep, require_isolation_receipt
from labs.ch08_measure.ledger import SealedLedger, hash_entry
from labs.ch08_measure.metric_card import evaluate_metric_card, load_metric_card
from labs.ch08_measure.token_roi import compute_token_roi, gate_token_roi
from labs.ch10_ecosystem.kill_rollback import KillSwitch

ROOT = Path(__file__).resolve().parents[3]
LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _signed_receipt(*, clean: bool = True, lineage_id: str = LINEAGE) -> dict:
    return issue_receipt(
        lineage_id=lineage_id,
        profile=default_lab_profile(),
        diff_paths=["adapters/x/"],
        clean=clean,
    ).to_dict()


def _cand(**overrides: object) -> dict:
    base = {
        "lineage_id": LINEAGE,
        "surface": "model",
        "hypothesis": "Improve held-out accuracy",
        "metric": "held_out",
        "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
        "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
        "proposer_role": "implementer",
        "isolation_receipt": _signed_receipt(),
    }
    base.update(overrides)
    return base


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
    finding = adversary_pass(
        _cand(
            hypothesis="rewrite evaluator secretly",
            diff={"paths": ["eval/scorer.py"], "summary": "bad"},
        )
    )
    assert finding.passed is False


def test_refuse_missing_isolation_receipt() -> None:
    cand = _cand()
    del cand["isolation_receipt"]
    ok, findings = require_isolation_receipt(cand)
    assert ok is False
    assert any("missing isolation_receipt" in f for f in findings)

    ledger = SealedLedger()
    sealed = evaluate_keep(
        cand,
        ledger,
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
    )
    assert sealed["decision"] == "reject"
    assert "missing isolation_receipt" in (sealed.get("notes") or "")


def test_refuse_forged_isolation_receipt() -> None:
    forged = {"receipt_id": "rcpt-forged", "clean": True, "lineage_id": LINEAGE}
    ok, findings = require_isolation_receipt(_cand(isolation_receipt=forged))
    assert ok is False
    assert any("signature invalid" in f for f in findings)

    sealed = evaluate_keep(
        _cand(isolation_receipt=forged),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
    )
    assert sealed["decision"] == "reject"
    assert "signature invalid" in (sealed.get("notes") or "")


def test_refuse_dirty_isolation_receipt() -> None:
    sealed = evaluate_keep(
        _cand(isolation_receipt=_signed_receipt(clean=False)),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
    )
    assert sealed["decision"] == "reject"
    assert "not clean" in (sealed.get("notes") or "")


def test_refuse_receipt_store_miss() -> None:
    receipt = _signed_receipt()
    sealed = evaluate_keep(
        _cand(isolation_receipt=receipt),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
        receipt_store={},
    )
    assert sealed["decision"] == "reject"
    assert "not found" in (sealed.get("notes") or "")


def test_evaluate_keep_accept_path_signed_receipt() -> None:
    receipt = _signed_receipt()
    store = {receipt["receipt_id"]: receipt}
    ledger = SealedLedger()
    sealed = evaluate_keep(
        _cand(isolation_receipt=receipt),
        ledger,
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        keep_threshold=0.5,
        tokens_used=1000,
        ablation_module_scores={"adapter": 0.0},
        receipt_store=store,
    )
    assert sealed["decision"] == "keep"
    assert sealed["scores"]["held_out"] == 1.0
    assert ledger.verify_chain()


def test_refuse_missing_ablation_when_required() -> None:
    sealed = evaluate_keep(
        _cand(),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores=None,
    )
    assert sealed["decision"] == "reject"
    assert "ablation" in (sealed.get("notes") or "").lower()


def test_token_roi_gate_refuses_low_roi() -> None:
    assert compute_token_roi(utility_gain=1.0, tokens_used=1000.0) == 0.001
    gate = gate_token_roi(held_out=0.1, tokens_used=1000.0, min_roi=0.01)
    assert gate["passed"] is False


def test_tampered_chain_fails_verify() -> None:
    ledger = SealedLedger()
    ledger.seal(
        lineage_id=LINEAGE,
        decision="keep",
        metric_card_id="card-1",
        repro_script="running_lab/repro.py",
    )
    ledger.entries[0]["entry_hash"] = "0" * 64
    assert ledger.verify_chain() is False


def test_hash_entry_deterministic() -> None:
    payload = {
        "lineage_id": LINEAGE,
        "decision": "reject",
        "score_authority": "external_evaluator",
        "metric_card_id": "c",
        "scores": {},
        "repro_script": "r.py",
        "notes": "",
    }
    assert hash_entry("GENESIS", payload) == hash_entry("GENESIS", payload)


def test_refuse_ablation_failure() -> None:
    sealed = evaluate_keep(
        _cand(),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 2.0},  # exceeds held-out → gaming signal
    )
    assert sealed["decision"] == "reject"
    assert "ablation" in (sealed.get("notes") or "")


def test_kill_switch_blocks_evaluate_keep() -> None:
    kill = KillSwitch()
    kill.kill("test")
    sealed = evaluate_keep(
        _cand(),
        SealedLedger(),
        metric_card_path=ROOT / "fixtures/metric_cards/lab_metric_card.json",
        dataset_root=ROOT / "fixtures/datasets",
        ablation_module_scores={"adapter": 0.0},
        kill_switch=kill,
    )
    assert sealed["decision"] == "reject"
    assert "kill switch" in (sealed.get("notes") or "")
