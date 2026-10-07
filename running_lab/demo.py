"""Dry-run CLI exercising the governed RSI loop."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from lab02_proposals_model.lora_candidate import forgetting_gate, make_stub_lora
from lab02_proposals_model.proposal_engine import build_proposal
from lab03_data_orchestration.harness_mutate import HarnessStore
from lab04_isolation_eval.eval_service import SealedLedger, evaluate_keep
from lab04_isolation_eval.sandbox import (
    SandboxViolation,
    assert_sandbox_allows,
    default_lab_profile,
)
from lab05_promotion_ecosystem.kill_rollback import KillSwitch, kill_and_rollback
from lab05_promotion_ecosystem.promotion_gateway import PromotionError, promote
from rsi_core.lineage import reset_registry
from rsi_core.types import Surface

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
        }
    ],
    "locked": [
        "eval/",
        "evaluators/",
        "held_out/",
        "metric_cards/",
        "ledger/",
        "schemas/",
        "CONTRACTS.md",
    ],
}


def run_dry_run(*, verbose: bool = True) -> dict[str, Any]:
    """Exercise propose → sandbox → eval keep → blocked promote → kill/rollback."""
    reset_registry()
    steps: list[dict[str, Any]] = []

    proposal = build_proposal(
        surface=Surface.MODEL,
        hypothesis="Stub adapter improves held-out proxy without touching eval",
        metric="held_out_proxy",
        paths=["adapters/candidate_v1/"],
        summary="stub LoRA envelope only",
        rollback_unit="adapters.candidate_v1",
        snapshot_ref="snap://adapters/candidate_v1@0",
        proposer_role="implementer",
        ownership_manifest=SAMPLE_MANIFEST,
    )
    steps.append({"step": "propose", "ok": True, "lineage_id": proposal["lineage_id"]})

    lora = make_stub_lora(proposal["lineage_id"])
    gate = forgetting_gate(lora, {"task_a": 0.79, "task_b": 0.74})
    steps.append({"step": "forgetting_gate", "ok": gate.passed, "message": gate.message})

    profile = default_lab_profile()
    assert_sandbox_allows(proposal["diff"]["paths"], profile)
    blocked = False
    try:
        assert_sandbox_allows(["eval/scorer.py"], profile)
    except SandboxViolation:
        blocked = True
    steps.append({"step": "sandbox", "ok": blocked, "blocked_evaluator_path": blocked})

    ledger = SealedLedger()
    decision = evaluate_keep(
        proposal,
        ledger,
        held_out_score=0.72,
        keep_threshold=0.5,
    )
    steps.append(
        {
            "step": "eval",
            "ok": decision["decision"] == "keep",
            "decision": decision["decision"],
            "entry_hash": decision["entry_hash"],
            "chain_ok": ledger.verify_chain(),
        }
    )

    promote_blocked = False
    try:
        promote(
            lineage_id=proposal["lineage_id"],
            sealed_decision=decision,
            token=None,
        )
    except PromotionError:
        promote_blocked = True
    steps.append(
        {
            "step": "promote_without_token",
            "ok": promote_blocked,
            "blocked": promote_blocked,
        }
    )

    harness = HarnessStore(modules={"planner": {"lr": 0.1}})
    harness.mutate("planner", {"lr": 0.5})
    kill = KillSwitch()
    result = kill_and_rollback(kill, harness, reason="demo dry-run complete")
    steps.append(
        {
            "step": "kill_rollback",
            "ok": result["kill_engaged"] and harness.modules["planner"]["lr"] == 0.1,
            "result": result,
        }
    )

    summary = {
        "dry_run": True,
        "all_ok": all(s["ok"] for s in steps),
        "steps": steps,
    }
    if verbose:
        print(json.dumps(summary, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GRSI running lab demo (stub envelopes only)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exercise propose→sandbox→eval→blocked promote→kill/rollback",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress JSON stdout (still returns exit code)",
    )
    # Console script `grsi-demo` may be invoked with no flags.
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        raw = ["--dry-run"]
    args = parser.parse_args(raw)
    if not args.dry_run:
        parser.error("Specify --dry-run (only supported mode in this stub)")
    summary = run_dry_run(verbose=not args.quiet)
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
