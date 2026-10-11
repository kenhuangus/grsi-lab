"""End-to-end local lab run of the governed RSI loop (real artifacts + gates)."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from labs.ch03_proposals.reject_gates import build_proposal
from labs.ch04_model_surface.adapter_package import make_adapter_candidate
from labs.ch04_model_surface.forgetting_gate import forgetting_gate
from labs.ch06_orchestration import HarnessStore
from labs.ch07_isolation import (
    ReceiptStore,
    SandboxViolation,
    assert_sandbox_allows,
    default_lab_profile,
    run_isolated,
)
from labs.ch08_measure import SealedLedger, evaluate_keep
from labs.ch09_promotion import PromotionError, promote, run_frozen_policy_scan
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token
from labs.ch10_ecosystem import KillSwitch, PublicationGate, kill_and_rollback
from rsi_core.compute_budget import ComputeBudgetLedger
from rsi_core.durable_store import DurableStore
from rsi_core.lineage import reset_registry
from rsi_core.types import Surface

ROOT = Path(__file__).resolve().parents[1]

SAMPLE_MANIFEST: dict[str, Any] = {
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
    ],
}


def run_lab(*, verbose: bool = True, work_dir: Path | None = None) -> dict[str, Any]:
    """Exercise propose → sandbox jail → metric eval → blocked/signed promote → kill."""
    reset_registry()
    steps: list[dict[str, Any]] = []
    base = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="grsi-lab-run-"))
    base.mkdir(parents=True, exist_ok=True)
    store = DurableStore(base / "grsi.sqlite3")
    ledger = SealedLedger(store=store)

    proposal = build_proposal(
        surface=Surface.MODEL,
        hypothesis="Adapter improves held-out accuracy without touching eval surfaces",
        metric="held_out_accuracy",
        paths=["adapters/candidate_v1/"],
        summary="on-disk adapter artifact with sha256 digests",
        rollback_unit="adapters.candidate_v1",
        snapshot_ref="snap://adapters/candidate_v1@0",
        proposer_role="implementer",
        ownership_manifest=SAMPLE_MANIFEST,
    )
    steps.append({"step": "propose", "ok": True, "lineage_id": proposal["lineage_id"]})

    adapter_dir = base / "adapters" / "candidate_v1"
    envelope = make_adapter_candidate(proposal["lineage_id"], adapter_dir)
    # Prior-task scores come from the same metric evaluator surface in production;
    # here we use verified artifact + explicit measured post scores.
    gate = forgetting_gate(envelope, {"task_a": 0.79, "task_b": 0.74})
    steps.append(
        {
            "step": "adapter_and_forgetting_gate",
            "ok": gate.passed,
            "weights_sha256": envelope.weights_sha256,
            "message": gate.message,
        }
    )

    profile = default_lab_profile()
    receipt_store = ReceiptStore(base / "receipts")
    isolated = run_isolated(
        {
            **proposal,
            "paths": list(proposal["diff"]["paths"]),
            "tenant_id": "lab",
        },
        profile=profile,
        receipt_store=receipt_store,
    )
    blocked = False
    try:
        assert_sandbox_allows(
            ["eval/scorer.py"], profile, jail_root=isolated.jail_root
        )
    except SandboxViolation:
        blocked = True
    steps.append(
        {
            "step": "sandbox_jail",
            "ok": isolated.ok and blocked,
            "jail": isolated.jail_root,
            "isolation_reason": isolated.reason,
        }
    )

    budget = ComputeBudgetLedger()
    spend = budget.authorize_spend(
        {
            "lineage_id": proposal["lineage_id"],
            "budget": {"units": "wall_seconds", "amount": 120},
            "target_metric": "held_out_accuracy",
            "stop_rule": "max_wall_seconds_or_threshold",
        },
        amount=12.0,
    )
    steps.append({"step": "compute_budget", "ok": spend["status"] == "authorized", "spend": spend})

    if not isolated.ok or isolated.receipt is None:
        steps.append(
            {
                "step": "eval_metric_card",
                "ok": False,
                "decision": "reject",
                "notes": isolated.reason,
            }
        )
        summary = {
            "lab_run": True,
            "work_dir": str(base),
            "all_ok": False,
            "steps": steps,
        }
        if verbose:
            print(json.dumps(summary, indent=2))
        store.close()
        return summary

    proposal["isolation_receipt"] = isolated.receipt.to_dict()
    decision = evaluate_keep(
        proposal,
        ledger,
        metric_card_path=ROOT / "fixtures" / "metric_cards" / "lab_metric_card.json",
        dataset_root=ROOT / "fixtures" / "datasets",
        keep_threshold=0.5,
        tokens_used=1000.0,
        ablation_module_scores={"adapter": 0.0},
        receipt_store=receipt_store,
    )
    sealed_path = base / "sealed_decision.json"
    sealed_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    steps.append(
        {
            "step": "eval_metric_card",
            "ok": decision["decision"] in {"keep", "revert", "reject"} and ledger.verify_chain(),
            "decision": decision["decision"],
            "scores": decision.get("scores"),
            "entry_hash": decision["entry_hash"],
            "chain_ok": ledger.verify_chain(),
            "sealed_path": str(sealed_path),
        }
    )

    promote_blocked = False
    try:
        promote(
            lineage_id=proposal["lineage_id"],
            sealed_decision=decision,
            token=None,
            ownership_manifest=SAMPLE_MANIFEST,
            candidate=proposal,
            ledger=ledger,
        )
    except PromotionError:
        promote_blocked = True
    steps.append({"step": "promote_without_token", "ok": promote_blocked})

    promoted_ok = False
    promote_result: dict[str, Any] | None = None
    record_store = PromotionRecordStore(base / "promotions")
    if decision["decision"] == "keep":
        scan = run_frozen_policy_scan(
            candidate=proposal,
            ownership_manifest=SAMPLE_MANIFEST,
            sealed_decision=decision,
        )
        token = mint_risk_tier_token(
            token_id="tok-lab-1",
            lineage_id=proposal["lineage_id"],
            human_signer="lab-operator",
            risk_tier="low",
            scan_report_hash=scan["report_hash"],
            frozen_policy_scan_passed=bool(scan["passed"]),
        )
        promote_result = promote(
            lineage_id=proposal["lineage_id"],
            sealed_decision=decision,
            token=token,
            ownership_manifest=SAMPLE_MANIFEST,
            candidate=proposal,
            ledger=ledger,
            record_store=record_store,
        )
        promoted_ok = (
            promote_result["status"] == "promoted"
            and promote_result.get("promotion_record_persisted") is True
        )
        steps.append(
            {
                "step": "promote_with_signed_token",
                "ok": promoted_ok,
                "result": promote_result,
            }
        )
        pub = PublicationGate(partner_allowlist={"lab-partner"})
        published = pub.publish(
            artifact_id="adapters/candidate_v1",
            partner="lab-partner",
            promotion_result=promote_result,
            lineage_id=proposal["lineage_id"],
            record_store=record_store,
        )
        steps.append(
            {
                "step": "publish_with_verified_token",
                "ok": published["status"] == "published",
                "result": published,
            }
        )
    else:
        steps.append({"step": "promote_with_signed_token", "ok": True, "skipped": True})
        steps.append({"step": "publish_with_verified_token", "ok": True, "skipped": True})

    harness = HarnessStore(modules={"planner": {"lr": 0.1}})
    harness.mutate("planner", {"lr": 0.5})
    kill = KillSwitch()
    result = kill_and_rollback(kill, harness, reason="lab run complete")
    steps.append(
        {
            "step": "kill_rollback",
            "ok": result["kill_engaged"] and harness.modules["planner"]["lr"] == 0.1,
            "result": result,
        }
    )

    summary = {
        "lab_run": True,
        "work_dir": str(base),
        "all_ok": all(s["ok"] for s in steps),
        "steps": steps,
    }
    if verbose:
        print(json.dumps(summary, indent=2))
    store.close()
    return summary


def run_dry_run(*, verbose: bool = True) -> dict[str, Any]:
    """Backward-compatible name — executes the full local lab run."""
    return run_lab(verbose=verbose)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GRSI running lab (real local gates)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compatibility flag; runs the local lab without external network",
    )
    parser.add_argument("--lab", action="store_true", help="Run the local governed lab")
    parser.add_argument("--quiet", action="store_true", help="Suppress JSON stdout")
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        raw = ["--lab"]
    args = parser.parse_args(raw)
    if not (args.dry_run or args.lab):
        parser.error("Specify --lab (or --dry-run compatibility alias)")
    summary = run_lab(verbose=not args.quiet)
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
