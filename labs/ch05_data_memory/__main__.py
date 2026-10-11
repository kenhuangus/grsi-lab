"""CLI for Chapter 5 data/memory lab gates."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from labs.ch05_data_memory.admit_experience import AdmissionPolicy, admit_experience
from labs.ch05_data_memory.broker_client import ExperienceBroker
from labs.ch05_data_memory.diversity_floor import DiversityFloor, check_diversity_floor
from labs.ch05_data_memory.gvc_pipeline import GVCPipeline
from labs.ch05_data_memory.token_roi_gate import TokenROIGate, evaluate_token_roi

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _cmd_admit(args: argparse.Namespace) -> int:
    record = json.loads(Path(args.record).read_text(encoding="utf-8"))
    policy = AdmissionPolicy(min_quality=args.min_quality)
    result = admit_experience(record, policy)
    print(json.dumps({"admitted": result.admitted, "reason": result.reason}, indent=2))
    return 0 if result.admitted else 1


def _cmd_broker_demo(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="grsi-ch05-") as tmp:
        broker = ExperienceBroker(Path(tmp), policy=AdmissionPolicy(min_quality=0.5))
        good = {
            "lineage_id": LINEAGE,
            "payload": {"text": "tool failed on missing schema field inventory_id"},
            "quality": 0.9,
            "tags": ["tool_error"],
            "module_id": "planner",
        }
        broker.quarantine_write(good)
        accepted = broker.admit_from_quarantine(good)
        bad = {
            "lineage_id": LINEAGE,
            "payload": "leak held_out labels into memory",
            "quality": 1.0,
            "tags": ["eval_leak"],
        }
        broker.quarantine_write(bad)
        refused = broker.admit_from_quarantine(bad)
        print(
            json.dumps(
                {
                    "accepted": accepted.admitted,
                    "accepted_reason": accepted.reason,
                    "refused": refused.admitted,
                    "refused_reason": refused.reason,
                    "admitted_count": broker.current_count,
                },
                indent=2,
            )
        )
        return 0 if accepted.admitted and not refused.admitted else 1


def _cmd_gvc_demo(_: argparse.Namespace) -> int:
    def validator(rec: dict[str, Any]) -> float:
        return float(rec.get("quality", 0.0))

    pipe = GVCPipeline(validator=validator, quality_floor=0.5)
    batch = [
        {
            "lineage_id": LINEAGE,
            "payload": f"distinct trajectory note about tool path {i} and schema field inventory",
            "quality": 0.9,
            "tags": ["tool_error", f"topic_{i % 3}"],
        }
        for i in range(6)
    ]
    result = pipe.run(batch)
    print(
        json.dumps(
            {
                "kept": result.kept,
                "reason": result.reason,
                "curated": len(result.curated),
                "corpus_root": result.corpus_root,
            },
            indent=2,
        )
    )
    return 0 if result.kept else 1


def _cmd_diversity_refuse(_: argparse.Namespace) -> int:
    floor = DiversityFloor(min_unique_ngram_ratio=0.9, max_duplicate_fingerprint_ratio=0.1)
    batch = [
        {"payload": "same note same note same note", "tags": ["a"]},
        {"payload": "same note same note same note", "tags": ["a"]},
    ]
    report = check_diversity_floor(batch, floor)
    print(json.dumps({"passed": report.passed, "reason": report.reason}, indent=2))
    return 0 if not report.passed else 1


def _cmd_token_roi(args: argparse.Namespace) -> int:
    gate = TokenROIGate(
        min_success_rate=args.min_success,
        max_mean_tokens=args.max_tokens,
        max_p95_latency_ms=args.max_latency,
    )
    tags = set(args.tags.split(",")) if args.tags else set()
    result = evaluate_token_roi(
        success_rate=args.success,
        mean_tokens=args.tokens,
        p95_latency_ms=args.latency,
        gate=gate,
        context_tags=tags,
    )
    print(json.dumps({"passed": result.passed, "reason": result.reason}, indent=2))
    return 0 if result.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m labs.ch05_data_memory")
    sub = parser.add_subparsers(dest="command", required=True)

    admit = sub.add_parser("admit", help="Admit one JSON experience record")
    admit.add_argument("--record", required=True)
    admit.add_argument("--min-quality", type=float, default=0.0)
    admit.set_defaults(func=_cmd_admit)

    broker = sub.add_parser("broker-demo", help="Happy + refuse broker path")
    broker.set_defaults(func=_cmd_broker_demo)

    gvc = sub.add_parser("gvc-demo", help="Run GVC on a diverse fixture batch")
    gvc.set_defaults(func=_cmd_gvc_demo)

    div = sub.add_parser("diversity-refuse", help="Show diversity floor refuse path")
    div.set_defaults(func=_cmd_diversity_refuse)

    roi = sub.add_parser("token-roi", help="Evaluate Token ROI band")
    roi.add_argument("--success", type=float, required=True)
    roi.add_argument("--tokens", type=float, required=True)
    roi.add_argument("--latency", type=float, required=True)
    roi.add_argument("--min-success", type=float, default=0.7)
    roi.add_argument("--max-tokens", type=float, default=4000.0)
    roi.add_argument("--max-latency", type=float, default=2000.0)
    roi.add_argument("--tags", default="")
    roi.set_defaults(func=_cmd_token_roi)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
