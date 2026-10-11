"""CLI for Chapter 7 isolation lab gates."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from labs.ch07_isolation.adversary_probes import run_adversary_probes
from labs.ch07_isolation.receipts import ReceiptStore
from labs.ch07_isolation.run_isolated import run_isolated
from labs.ch07_isolation.sandbox_profile import default_lab_profile
from labs.ch07_isolation.widening_guard import WideningViolation, assert_no_widening

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _cmd_run_clean(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="grsi-ch07-") as tmp:
        store = ReceiptStore(Path(tmp) / "receipts")
        result = run_isolated(
            {
                "lineage_id": LINEAGE,
                "paths": ["adapters/candidate/v1/model.safetensors"],
            },
            receipt_store=store,
        )
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "reason": result.reason,
                    "clean": result.receipt.clean if result.receipt else None,
                    "receipt_id": result.receipt.receipt_id if result.receipt else None,
                },
                indent=2,
            )
        )
        return 0 if result.ok else 1


def _cmd_run_refuse_held_out(_: argparse.Namespace) -> int:
    result = run_isolated(
        {
            "lineage_id": LINEAGE,
            "paths": ["skills/search.py", "held_out/labels.jsonl"],
        }
    )
    print(
        json.dumps(
            {
                "ok": result.ok,
                "reason": result.reason,
                "clean": result.receipt.clean if result.receipt else None,
            },
            indent=2,
        )
    )
    return 0 if (not result.ok and result.receipt and not result.receipt.clean) else 1


def _cmd_widening_refuse(_: argparse.Namespace) -> int:
    try:
        assert_no_widening(
            {
                "paths": ["configs/sandbox_profile.json"],
                "hypothesis": "open network via egress_allow for pypi",
                "profile_patch": {"egress_allow": ["pypi.org"]},
            },
            locked_profile=default_lab_profile(),
        )
        print(json.dumps({"refused": False}, indent=2))
        return 1
    except WideningViolation as exc:
        print(json.dumps({"refused": True, "reason": str(exc)}, indent=2))
        return 0


def _cmd_probes(_: argparse.Namespace) -> int:
    report = run_adversary_probes(default_lab_profile())
    print(
        json.dumps(
            {
                "passed": report.passed,
                "reason": report.reason,
                "denied_count": len(report.denied_probes),
            },
            indent=2,
        )
    )
    return 0 if report.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m labs.ch07_isolation")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("run-clean", help="Clean isolation receipt for allowlisted paths")
    c.set_defaults(func=_cmd_run_clean)

    r = sub.add_parser("run-refuse", help="Refuse held_out path contact")
    r.set_defaults(func=_cmd_run_refuse_held_out)

    w = sub.add_parser("widening-refuse", help="Refuse profile widening proposal")
    w.set_defaults(func=_cmd_widening_refuse)

    p = sub.add_parser("probes", help="Run default adversary path probes")
    p.set_defaults(func=_cmd_probes)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
