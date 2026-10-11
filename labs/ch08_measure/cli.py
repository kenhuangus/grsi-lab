"""CLI for Chapter 8 measure lab: adversary / evaluate_keep / ledger verify."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from labs.ch07_isolation.receipts import ReceiptStore, issue_receipt
from labs.ch07_isolation.run_isolated import run_isolated
from labs.ch07_isolation.sandbox_profile import default_lab_profile
from labs.ch08_measure.adversary_pass import adversary_pass
from labs.ch08_measure.evaluate_keep import evaluate_keep
from labs.ch08_measure.ledger import SealedLedger

ROOT = Path(__file__).resolve().parents[2]


def _sample_candidate(
    *,
    dirty: bool = False,
    with_receipt: bool = True,
    receipt_root: Path | None = None,
) -> tuple[dict[str, Any], ReceiptStore | None]:
    lineage = str(uuid.uuid4())
    paths = ["eval/scorer.py"] if dirty else ["adapters/x/"]
    cand: dict[str, Any] = {
        "lineage_id": lineage,
        "surface": "model",
        "hypothesis": (
            "rewrite evaluator secretly" if dirty else "Improve held-out accuracy"
        ),
        "metric": "held_out",
        "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
        "diff": {
            "paths": paths,
            "summary": "bad" if dirty else "adapter",
        },
        "proposer_role": "implementer",
        "paths": paths,
        "tenant_id": "lab",
    }
    store: ReceiptStore | None = None
    if with_receipt:
        if dirty:
            # Dirty path: adversary candidate still needs a signed unclean receipt.
            receipt = issue_receipt(
                lineage_id=lineage,
                profile=default_lab_profile(),
                diff_paths=paths,
                clean=False,
            )
            cand["isolation_receipt"] = receipt.to_dict()
        else:
            # Clean path must come from run_isolated — never forge clean:true.
            store = ReceiptStore(receipt_root or (ROOT / "tmp" / "ch08_cli_receipts"))
            isolated = run_isolated(cand, receipt_store=store)
            if isolated.receipt is None:
                raise RuntimeError(f"isolation produced no receipt: {isolated.reason}")
            cand["isolation_receipt"] = isolated.receipt.to_dict()
    return cand, store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GRSI Ch8 measure lab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_adv = sub.add_parser("adversary", help="Run adversary pass (refuse path)")
    p_adv.add_argument("--dirty", action="store_true", help="Use a gaming candidate")

    p_eval = sub.add_parser("evaluate", help="Run evaluate_keep accept/refuse")
    p_eval.add_argument("--no-receipt", action="store_true", help="Omit isolation receipt")
    p_eval.add_argument("--dirty", action="store_true", help="Use a gaming candidate")
    p_eval.add_argument("--threshold", type=float, default=0.5)

    sub.add_parser("verify-ledger", help="Seal two entries and verify chain")

    args = parser.parse_args(argv)
    if args.cmd == "adversary":
        cand, _ = _sample_candidate(dirty=args.dirty)
        finding = adversary_pass(cand)
        print(json.dumps({"passed": finding.passed, "findings": finding.findings}, indent=2))
        return 0 if finding.passed else 1

    if args.cmd == "evaluate":
        cand, receipt_store = _sample_candidate(
            dirty=args.dirty, with_receipt=not args.no_receipt
        )
        ledger = SealedLedger()
        sealed = evaluate_keep(
            cand,
            ledger,
            metric_card_path=ROOT / "fixtures" / "metric_cards" / "lab_metric_card.json",
            dataset_root=ROOT / "fixtures" / "datasets",
            keep_threshold=args.threshold,
            tokens_used=1000.0,
            ablation_module_scores={"adapter": 0.0},
            receipt_store=receipt_store,
        )
        print(json.dumps(sealed, indent=2))
        ok = sealed["decision"] == "keep" and ledger.verify_chain()
        return 0 if ok else 1

    if args.cmd == "verify-ledger":
        ledger = SealedLedger()
        lid = str(uuid.uuid4())
        ledger.seal(
            lineage_id=lid,
            decision="keep",
            metric_card_id="card-1",
            repro_script="running_lab/repro.py",
            scores={"held_out": 0.9},
        )
        print(json.dumps({"verify_chain": ledger.verify_chain(), "tip": ledger.tip_hash}, indent=2))
        return 0 if ledger.verify_chain() else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
