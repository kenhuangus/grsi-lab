"""CLI for Chapter 4 model-surface lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from labs.ch04_model_surface.adapter_package import make_adapter_candidate
from labs.ch04_model_surface.cheapest_surface import CheaperAttempt, require_cheapest_surface
from labs.ch04_model_surface.forgetting_gate import forgetting_gate
from labs.ch04_model_surface.recipe_contract import (
    RecipeContractError,
    build_recipe_contract,
    recipe_canonical_hash,
)
from labs.ch04_model_surface.train_job_record import TrainJobError, open_train_job


def cmd_package(args: argparse.Namespace) -> int:
    package = make_adapter_candidate(
        args.lineage_id,
        args.adapter_dir,
        base_model_ref=args.base_model_ref,
        adapter_name=args.adapter_name,
        rank=args.rank,
    )
    print(json.dumps({"ok": True, "package": package.to_dict()}, indent=2))
    return 0


def cmd_forget(args: argparse.Namespace) -> int:
    package = make_adapter_candidate(args.lineage_id, args.adapter_dir)
    posts = json.loads(Path(args.post_scores).read_text(encoding="utf-8"))
    if args.threshold is not None:
        package.forgetting_gate_threshold = args.threshold
    result = forgetting_gate(package, posts)
    print(
        json.dumps(
            {
                "ok": result.passed,
                "message": result.message,
                "regressions": result.regressions,
            },
            indent=2,
        )
    )
    return 0 if result.passed else 1


def cmd_escalate(args: argparse.Namespace) -> int:
    attempts_raw = json.loads(Path(args.attempts).read_text(encoding="utf-8"))
    attempts = [CheaperAttempt(**row) for row in attempts_raw]
    harness = (
        json.loads(Path(args.harness_candidates).read_text(encoding="utf-8"))
        if args.harness_candidates
        else []
    )
    experience = (
        json.loads(Path(args.experience_candidates).read_text(encoding="utf-8"))
        if args.experience_candidates
        else []
    )
    decision = require_cheapest_surface(
        metric=args.metric,
        failure_statement=args.failure,
        cheaper_attempts=attempts,
        harness_candidates=list(harness),
        experience_candidates=list(experience),
    )
    print(
        json.dumps(
            {
                "ok": decision.allowed,
                "message": decision.message,
                "refusals": decision.refusals,
            },
            indent=2,
        )
    )
    return 0 if decision.allowed else 1


def cmd_recipe(args: argparse.Namespace) -> int:
    contract = build_recipe_contract(
        lineage_id=args.lineage_id,
        kind=args.kind,
        data_mix_id=args.data_mix_id,
        loss_name=args.loss_name,
        schedule=args.schedule,
        stop_rule=args.stop_rule,
        preference_source=args.preference_source,
        judge_ref=args.judge_ref,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "recipe": contract.to_dict(),
                "hash": recipe_canonical_hash(contract),
            },
            indent=2,
        )
    )
    return 0


def cmd_train_job(args: argparse.Namespace) -> int:
    package = make_adapter_candidate(args.lineage_id, args.adapter_dir)
    recipe = build_recipe_contract(
        lineage_id=args.lineage_id,
        kind=args.kind,
        data_mix_id=args.data_mix_id,
        loss_name=args.loss_name,
        schedule=args.schedule,
        stop_rule=args.stop_rule,
        preference_source=args.preference_source,
        judge_ref=args.judge_ref,
    )
    record = open_train_job(
        package=package,
        recipe=recipe,
        metric_card_id=args.metric_card_id,
        metric_card_sha256=args.metric_card_sha256,
        sandbox_profile_id=args.sandbox_profile_id,
    )
    print(json.dumps({"ok": True, "job": record.to_dict()}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m labs.ch04_model_surface",
        description="Chapter 4 model-surface lab: adapter, forgetting, escalate, recipe",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pkg = sub.add_parser("package", help="Write and verify an adapter package")
    p_pkg.add_argument("--lineage-id", required=True)
    p_pkg.add_argument("--adapter-dir", required=True)
    p_pkg.add_argument("--base-model-ref", default="hf://example/base-model")
    p_pkg.add_argument("--adapter-name", default="candidate-adapter")
    p_pkg.add_argument("--rank", type=int, default=8)
    p_pkg.set_defaults(func=cmd_package)

    p_fg = sub.add_parser("forget", help="Run forgetting gate against post scores JSON")
    p_fg.add_argument("--lineage-id", required=True)
    p_fg.add_argument("--adapter-dir", required=True)
    p_fg.add_argument("--post-scores", required=True)
    p_fg.add_argument("--threshold", type=float, default=None)
    p_fg.set_defaults(func=cmd_forget)

    p_es = sub.add_parser("escalate", help="Cheapest-surface gate before model open")
    p_es.add_argument("--metric", required=True)
    p_es.add_argument("--failure", required=True)
    p_es.add_argument("--attempts", required=True, help="JSON list of CheaperAttempt dicts")
    p_es.add_argument(
        "--harness-candidates",
        default=None,
        help="JSON list of harness candidate ids/paths",
    )
    p_es.add_argument(
        "--experience-candidates",
        default=None,
        help="JSON list of experience candidate ids/paths",
    )
    p_es.set_defaults(func=cmd_escalate)

    p_rc = sub.add_parser("recipe", help="Build a recipe contract and hash")
    p_rc.add_argument("--lineage-id", required=True)
    p_rc.add_argument("--kind", required=True, choices=["sft", "dpo", "rlaif"])
    p_rc.add_argument("--data-mix-id", required=True)
    p_rc.add_argument("--loss-name", required=True)
    p_rc.add_argument("--schedule", required=True)
    p_rc.add_argument("--stop-rule", required=True)
    p_rc.add_argument("--preference-source", default=None)
    p_rc.add_argument("--judge-ref", default=None)
    p_rc.set_defaults(func=cmd_recipe)

    p_tj = sub.add_parser("train-job", help="Open a pinned train-job record")
    p_tj.add_argument("--lineage-id", required=True)
    p_tj.add_argument("--adapter-dir", required=True)
    p_tj.add_argument("--kind", default="sft", choices=["sft", "dpo", "rlaif"])
    p_tj.add_argument("--data-mix-id", required=True)
    p_tj.add_argument("--loss-name", required=True)
    p_tj.add_argument("--schedule", required=True)
    p_tj.add_argument("--stop-rule", required=True)
    p_tj.add_argument("--preference-source", default=None)
    p_tj.add_argument("--judge-ref", default=None)
    p_tj.add_argument("--metric-card-id", required=True)
    p_tj.add_argument("--metric-card-sha256", required=True)
    p_tj.add_argument("--sandbox-profile-id", required=True)
    p_tj.set_defaults(func=cmd_train_job)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (RecipeContractError, TrainJobError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
