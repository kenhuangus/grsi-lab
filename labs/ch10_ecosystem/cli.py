"""CLI for Chapter 10 ecosystem lab."""

from __future__ import annotations

import argparse
import json
import sys

from labs.ch10_ecosystem.dry_run import run_ecosystem_dry_run
from labs.ch10_ecosystem.failure_atlas import by_loop_step, load_entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GRSI Ch10 ecosystem lab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dry-run", help="Local ecosystem dry-run (no network)")
    p_atlas = sub.add_parser("atlas", help="List failure atlas entries for a loop step")
    p_atlas.add_argument(
        "--step",
        default="promote",
        choices=[
            "propose",
            "isolate",
            "verify_measure",
            "keep_revert",
            "archive",
            "promote",
            "audit",
        ],
    )
    args = parser.parse_args(argv)

    if args.cmd == "dry-run":
        summary = run_ecosystem_dry_run()
        print(json.dumps(summary, indent=2))
        return 0 if summary["all_ok"] else 1

    entries = by_loop_step(load_entries(), args.step)
    print(json.dumps({"step": args.step, "count": len(entries), "entries": entries}, indent=2))
    return 0 if entries else 1


if __name__ == "__main__":
    sys.exit(main())
