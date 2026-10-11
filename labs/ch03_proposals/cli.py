"""CLI for Chapter 3 proposals lab."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from labs.ch03_proposals.compute_request import (
    ComputeBudgetError,
    ComputeBudgetLedger,
    authorize_compute,
    build_compute_request,
)
from labs.ch03_proposals.lineage import assert_shared_lineage, close_proposal_lineage
from labs.ch03_proposals.planner import plan_then_implement
from labs.ch03_proposals.reject_gates import ProposalRejectError, build_proposal
from rsi_core.ownership import load_manifest
from rsi_core.types import LockedPathError, Surface


def cmd_plan_implement(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    planner, implementer = plan_then_implement(
        args.hypothesis,
        args.summary,
        metric=args.metric,
        paths=args.paths,
        rollback_unit=args.rollback_unit,
        snapshot_ref=args.snapshot_ref,
        ownership_manifest=manifest,
        surface=Surface(args.surface),
        require_manifest=True,
    )
    shared = assert_shared_lineage(planner, implementer)
    print(
        json.dumps(
            {
                "ok": True,
                "lineage_id": shared,
                "planner": planner,
                "implementer": implementer,
            },
            indent=2,
        )
    )
    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    envelope = build_proposal(
        surface=Surface(args.surface),
        hypothesis=args.hypothesis,
        metric=args.metric,
        paths=args.paths,
        summary=args.summary,
        rollback_unit=args.rollback_unit,
        snapshot_ref=args.snapshot_ref,
        proposer_role=args.role,
        ownership_manifest=manifest,
        require_manifest=True,
    )
    print(json.dumps({"ok": True, "envelope": envelope}, indent=2))
    return 0


def cmd_compute(args: argparse.Namespace) -> int:
    request = build_compute_request(
        lineage_id=args.lineage_id,
        units=args.units,
        amount=args.amount,
        target_metric=args.target_metric,
        stop_rule=args.stop_rule,
    )
    if args.spend is not None:
        # One ledger per CLI invocation — callers that need multi-spend cumulative
        # accounting must reuse a ledger in-process (see authorize_compute).
        ledger = ComputeBudgetLedger()
        out = authorize_compute(request, amount=args.spend, ledger=ledger)
        print(json.dumps({"ok": True, "request": request, "authorization": out}, indent=2))
    else:
        print(json.dumps({"ok": True, "request": request}, indent=2))
    return 0


def cmd_close_lineage(args: argparse.Namespace) -> int:
    record = close_proposal_lineage(
        args.lineage_id,
        args.decision,
        reason=args.reason,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "lineage_id": record.lineage_id,
                "status": record.status.value,
                "close_reason": record.close_reason,
                "closed_at": record.closed_at,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m labs.ch03_proposals",
        description="Chapter 3 proposals lab: planner/implementer, rejects, compute",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--manifest", required=True)
        p.add_argument("--hypothesis", required=True)
        p.add_argument("--metric", required=True)
        p.add_argument("--paths", nargs="+", required=True)
        p.add_argument("--rollback-unit", required=True)
        p.add_argument("--snapshot-ref", required=True)
        p.add_argument(
            "--surface",
            default="model",
            choices=[s.value for s in Surface],
        )

    p_pi = sub.add_parser("plan-implement", help="Planner then implementer under one lineage")
    add_common(p_pi)
    p_pi.add_argument("--summary", required=True, help="Implementer diff summary")
    p_pi.set_defaults(func=cmd_plan_implement)

    p_pr = sub.add_parser("propose", help="Single-role proposal")
    add_common(p_pr)
    p_pr.add_argument("--summary", required=True)
    p_pr.add_argument(
        "--role",
        default="planner",
        choices=["planner", "implementer", "in_harness_verifier"],
    )
    p_pr.set_defaults(func=cmd_propose)

    p_c = sub.add_parser("compute", help="Build/authorize a compute_request")
    p_c.add_argument("--lineage-id", required=True)
    p_c.add_argument(
        "--units",
        required=True,
        choices=["gpu_hours", "tokens", "wall_seconds", "dollars"],
    )
    p_c.add_argument("--amount", type=float, required=True)
    p_c.add_argument("--target-metric", required=True)
    p_c.add_argument("--stop-rule", required=True)
    p_c.add_argument("--spend", type=float, default=None)
    p_c.set_defaults(func=cmd_compute)

    p_cl = sub.add_parser(
        "close-lineage",
        help="Close a proposal lineage at keep/revert/reject",
    )
    p_cl.add_argument("--lineage-id", required=True)
    p_cl.add_argument(
        "--decision",
        required=True,
        choices=["keep", "revert", "reject"],
    )
    p_cl.add_argument("--reason", default=None)
    p_cl.set_defaults(func=cmd_close_lineage)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (
        ProposalRejectError,
        LockedPathError,
        ComputeBudgetError,
        ValueError,
        OSError,
        KeyError,
    ) as exc:
        payload: dict[str, Any] = {"ok": False, "error": str(exc)}
        if isinstance(exc, ProposalRejectError):
            payload["reject_class"] = exc.reject_class
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
