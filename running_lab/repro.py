"""Re-run metric-card evaluation and verify sealed scores are reproducible."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab04_isolation_eval.metric_eval import evaluate_metric_card, load_metric_card

ROOT = Path(__file__).resolve().parents[1]


def reproduce(
    *,
    sealed_path: Path,
    card_path: Path,
    dataset_root: Path,
    tokens_used: float = 1000.0,
    atol: float = 1e-9,
) -> dict:
    sealed = json.loads(sealed_path.read_text(encoding="utf-8"))
    card = load_metric_card(card_path)
    bundle = evaluate_metric_card(
        card,
        dataset_root=dataset_root,
        ablation_module_scores={"adapter": 0.0},
        tokens_used=tokens_used,
    )
    expected = sealed.get("scores") or {}
    mismatches = []
    for key, value in bundle.scores.items():
        if key not in expected:
            mismatches.append(f"missing sealed score: {key}")
            continue
        if abs(float(expected[key]) - float(value)) > atol:
            mismatches.append(f"{key}: sealed={expected[key]} repro={value}")
    return {
        "ok": not mismatches,
        "mismatches": mismatches,
        "repro_scores": bundle.scores,
        "sealed_scores": expected,
        "entry_hash": sealed.get("entry_hash"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce a sealed GRSI evaluation")
    parser.add_argument("--sealed", type=Path, required=True, help="Path to sealed_decision JSON")
    parser.add_argument(
        "--card",
        type=Path,
        default=ROOT / "fixtures" / "metric_cards" / "lab_metric_card.json",
    )
    parser.add_argument(
        "--datasets",
        type=Path,
        default=ROOT / "fixtures" / "datasets",
    )
    parser.add_argument("--tokens-used", type=float, default=1000.0)
    args = parser.parse_args(argv)
    result = reproduce(
        sealed_path=args.sealed,
        card_path=args.card,
        dataset_root=args.datasets,
        tokens_used=args.tokens_used,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
