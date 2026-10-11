"""CLI for Chapter 2 ownership lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from labs.ch02_ownership.blast_radius import assess_blast_radius
from labs.ch02_ownership.freeze_gate import FREEZE_CHECKLIST_ITEMS, run_freeze_gate
from labs.ch02_ownership.manifest import validate_manifest_file
from labs.ch02_ownership.reject_locked_writes import inspect_writes
from rsi_core.ownership import load_manifest
from rsi_core.types import LockedPathError


def _load_manifest_arg(path: str) -> dict[str, Any]:
    return load_manifest(path)


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_manifest_file(args.manifest)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "errors": []}, indent=2))
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    manifest = _load_manifest_arg(args.manifest)
    report = inspect_writes(args.paths, manifest, require_declared=True)
    payload = {
        "ok": report.accepted,
        "rejects": [
            {"path": r.path, "class": r.reject_class, "message": r.message}
            for r in report.rejects
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0 if report.accepted else 1


def cmd_freeze(args: argparse.Namespace) -> int:
    manifest = _load_manifest_arg(args.manifest)
    evidence: dict[str, bool] = {}
    evidence_paths: dict[str, Any] | None = None
    staging_all_evidence = False

    if args.evidence:
        raw = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("evidence JSON must be an object")
        evidence_paths = {}
        for key, value in raw.items():
            if isinstance(value, bool):
                evidence[key] = value
            elif isinstance(value, (str, dict)):
                evidence[key] = True
                evidence_paths[key] = value
            else:
                evidence[key] = bool(value)
        if not evidence_paths:
            evidence_paths = None
    elif args.all_evidence:
        staging_all_evidence = True
        print(
            "WARNING: --all-evidence is staging-only; bare checklist True "
            "without evidence_paths cannot pass the freeze gate. Prefer "
            "--evidence JSON with artifact paths.",
            file=sys.stderr,
        )
        evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    else:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "freeze accept requires --evidence JSON "
                        "(or staging-only --all-evidence with explicit warning)"
                    ),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    result = run_freeze_gate(
        manifest,
        evidence=evidence,
        evidence_paths=evidence_paths,
        break_ticket=args.break_ticket,
        break_paths=args.break_paths,
    )
    payload: dict[str, Any] = {
        "ok": result.passed,
        "status": result.status.value,
        "failures": result.failures,
        "message": result.message,
        "checklist": result.checklist,
    }
    if staging_all_evidence:
        payload["staging_all_evidence"] = True
        payload["warning"] = (
            "staging-only: --all-evidence hardcodes checklist True without artifacts"
        )
    print(json.dumps(payload, indent=2))
    return 0 if result.passed else 1


def cmd_blast(args: argparse.Namespace) -> int:
    manifest = _load_manifest_arg(args.manifest)
    evidence: dict[str, Any] | None = None
    if args.evidence:
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    assessment = assess_blast_radius(
        args.paths,
        manifest,
        declared_surface=args.surface,
        allow_infrastructure=args.allow_infra,
        evidence=evidence,
    )
    print(
        json.dumps(
            {
                "ok": assessment.accepted,
                "primary_surface": assessment.primary_surface,
                "surfaces": sorted(assessment.surfaces),
                "blast_rank": assessment.blast_rank,
                "required_evidence": assessment.required_evidence,
                "refusals": assessment.refusals,
                "message": assessment.message,
            },
            indent=2,
        )
    )
    return 0 if assessment.accepted else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m labs.ch02_ownership",
        description="Chapter 2 ownership lab: manifest, reject, freeze, blast radius",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate modularity of a manifest file")
    p_val.add_argument("--manifest", required=True)
    p_val.set_defaults(func=cmd_validate)

    p_rej = sub.add_parser("reject", help="Inspect write paths against ownership")
    p_rej.add_argument("--manifest", required=True)
    p_rej.add_argument("paths", nargs="+")
    p_rej.set_defaults(func=cmd_reject)

    p_fr = sub.add_parser("freeze", help="Run Last Frozen Layer freeze gate")
    p_fr.add_argument("--manifest", required=True)
    p_fr.add_argument(
        "--evidence",
        help="JSON file of checklist evidence (booleans and/or artifact paths)",
    )
    p_fr.add_argument(
        "--all-evidence",
        action="store_true",
        help="STAGING ONLY: hardcode every checklist item true (prints warning)",
    )
    p_fr.add_argument("--break-ticket", default=None)
    p_fr.add_argument("--break-paths", nargs="*", default=None)
    p_fr.set_defaults(func=cmd_freeze)

    p_bl = sub.add_parser("blast", help="Assess blast radius for candidate paths")
    p_bl.add_argument("--manifest", required=True)
    p_bl.add_argument("paths", nargs="+")
    p_bl.add_argument("--surface", default=None)
    p_bl.add_argument("--allow-infra", action="store_true")
    p_bl.add_argument(
        "--evidence",
        help="JSON file mapping required evidence keys to true/artifact values",
    )
    p_bl.set_defaults(func=cmd_blast)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (LockedPathError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
