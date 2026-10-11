"""CLI for Chapter 6 orchestration lab gates."""

from __future__ import annotations

import argparse
import json
import sys

from labs.ch06_orchestration.bi_level_loop import BiLevelLoop, make_fixture_scorer
from labs.ch06_orchestration.harness_store import HarnessStore
from labs.ch06_orchestration.role_graph import RoleGraph, RoleSpec
from labs.ch06_orchestration.schema_reload import SchemaReloadError, reload_tool_schema


def _cmd_mutate_demo(_: argparse.Namespace) -> int:
    store = HarnessStore(modules={"planner": {"lr": 0.1, "prompt": "base"}})
    store.mutate("planner", {"lr": 0.2, "prompt": "candidate"})
    rolled = store.rollback("planner")
    print(json.dumps({"restored_lr": rolled["lr"], "ok": rolled["lr"] == 0.1}, indent=2))
    return 0 if rolled["lr"] == 0.1 else 1


def _cmd_bi_level(args: argparse.Namespace) -> int:
    fixtures = {"base": 0.50, args.prompt: args.score}
    store = HarnessStore(
        modules={"planner": {"prompt": "base"}},
        backbone_pin="bb-1",
        require_registered_schema=True,
    )
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        noise_floor=0.01,
        max_policy_tokens=args.max_policy_tokens,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"prompt": args.prompt},
        tool_schema={"name": "search", "parameters": {"q": {"type": "string"}}},
        backbone_pin=args.backbone,
    )
    print(
        json.dumps(
            {
                "kept": result.kept,
                "reason": result.reason,
                "baseline": result.baseline_score,
                "candidate": result.candidate_score,
                "schema_version": store.accepted_schema_version,
            },
            indent=2,
        )
    )
    return 0 if result.kept else 1


def _cmd_schema_refuse(_: argparse.Namespace) -> int:
    try:
        reload_tool_schema(
            {
                "name": "shell",
                "parameters": {},
                "writable_paths": ["eval/scorer.py"],
            }
        )
        print(json.dumps({"refused": False}, indent=2))
        return 1
    except SchemaReloadError as exc:
        print(json.dumps({"refused": True, "reason": str(exc)}, indent=2))
        return 0


def _cmd_role_collapse(_: argparse.Namespace) -> int:
    graph = RoleGraph()
    for rid in ("chief", "specialist_a", "specialist_b"):
        graph.add_role(
            RoleSpec(
                role_id=rid,
                package_path=f"roles/{rid}",
                eval_hook=f"eval/{rid}",
                rollback_unit=f"roles.{rid}",
                instructions=f"instructions for {rid}",
            )
        )
    prior = len(graph.distinct_role_hashes())
    merge = graph.merge_roles("chief", "specialist_a", declared=False)
    collapse = graph.detect_role_collapse(prior_hash_count=prior)
    print(json.dumps({"merge": merge, "collapse": collapse}, indent=2))
    return 0 if (not merge["ok"] and not collapse["collapsed"]) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m labs.ch06_orchestration")
    sub = parser.add_subparsers(dest="command", required=True)

    m = sub.add_parser("mutate-demo", help="Mutate then rollback one module")
    m.set_defaults(func=_cmd_mutate_demo)

    b = sub.add_parser("bi-level", help="Run bi-level propose/evaluate")
    b.add_argument("--prompt", default="improved planner")
    b.add_argument(
        "--score",
        type=float,
        default=0.56,
        help="External fixture score for --prompt (not written into the patch)",
    )
    b.add_argument("--backbone", default="bb-1")
    b.add_argument("--max-policy-tokens", type=int, default=64)
    b.set_defaults(func=_cmd_bi_level)

    s = sub.add_parser("schema-refuse", help="Refuse schema that widens into eval/")
    s.set_defaults(func=_cmd_schema_refuse)

    r = sub.add_parser("role-collapse", help="Refuse undeclared role merge")
    r.set_defaults(func=_cmd_role_collapse)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
