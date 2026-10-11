"""CLI for Chapter 9 promotion lab."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from typing import Any

from labs.ch08_measure.ledger import SealedLedger
from labs.ch09_promotion.evidence_pack import build_evidence_pack
from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.promotion_gateway import PromotionError, promote
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token

MANIFEST: dict[str, Any] = {
    "version": "1.0",
    "components": [
        {
            "path": "adapters/x/",
            "owner": "lab",
            "eval_hook": "eval/score",
            "rollback_unit": "adapters.x",
            "observability_signal": "x_ok",
        }
    ],
    "locked": ["eval/", "held_out/", "ledger/", "CONTRACTS.md"],
}


def _candidate(lineage: str) -> dict[str, Any]:
    return {
        "lineage_id": lineage,
        "surface": "model",
        "hypothesis": "Improve held-out accuracy",
        "metric": "held_out",
        "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
        "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
        "proposer_role": "implementer",
        "isolation_receipt": {"receipt_id": "rcpt-1", "clean": True, "lineage_id": lineage},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GRSI Ch9 promotion lab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("refuse-no-token", help="Promote without token (must fail)")
    p_ok = sub.add_parser("promote", help="Seal keep + mint token + promote")
    p_ok.add_argument("--tier", default="low", choices=["low", "medium", "high", "critical"])
    args = parser.parse_args(argv)

    lineage = str(uuid.uuid4())
    cand = _candidate(lineage)
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=lineage,
        decision="keep",
        metric_card_id="lab-metric-card",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )

    if args.cmd == "refuse-no-token":
        try:
            promote(
                lineage_id=lineage,
                sealed_decision=sealed,
                token=None,
                ownership_manifest=MANIFEST,
                candidate=cand,
                ledger=ledger,
            )
        except PromotionError as exc:
            print(json.dumps({"ok": True, "refused": str(exc)}, indent=2))
            return 0
        print(json.dumps({"ok": False, "error": "expected PromotionError"}, indent=2))
        return 1

    scan = run_frozen_policy_scan(
        candidate=cand, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    pack = build_evidence_pack(
        sealed_decision=sealed, scan_report=scan, candidate=cand
    )
    if not scan["passed"]:
        print(
            json.dumps(
                {"ok": False, "error": "frozen policy scan failed", "scan": scan},
                indent=2,
            )
        )
        return 1
    token = mint_risk_tier_token(
        token_id="tok-cli-1",
        lineage_id=lineage,
        human_signer="lab-operator",
        risk_tier=args.tier,
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    try:
        result = promote(
            lineage_id=lineage,
            sealed_decision=sealed,
            token=token,
            ownership_manifest=MANIFEST,
            candidate=cand,
            ledger=ledger,
            record_store=PromotionRecordStore(),
        )
    except PromotionError as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc), "evidence_pack_hash": pack["pack_hash"]},
                indent=2,
            )
        )
        return 1
    print(json.dumps({"ok": True, "result": result, "evidence_pack": pack}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
