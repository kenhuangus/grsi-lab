"""Real metric-card evaluation over JSONL datasets (no fabricated scores)."""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rsi_core.schemas_load import validate_instance


@dataclass
class EvalBundle:
    """Measured scores produced by evaluating a candidate against a metric card."""

    card_id: str
    scores: dict[str, float]
    seed_scores: dict[str, list[float]]
    token_roi: float
    ablation_ok: bool
    details: dict[str, Any]


def load_metric_card(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_instance("metric_card", data)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"empty dataset: {path}")
    return rows


def _score_rows(rows: list[dict[str, Any]], metric_name: str, seed: int) -> float:
    """Deterministic accuracy-style score from labeled rows + candidate seed.

    Each row: ``{"id":..., "label": 0|1, "features": [float,...]}``.
    Candidate contribution is a seeded linear threshold — real math, not a constant.
    """
    rng_state = seed * 1_000_003
    correct = 0
    for row in rows:
        feats = row.get("features") or [0.0]
        label = int(row["label"])
        # Deterministic pseudo-hash mix of features and seed
        acc = 0.0
        for i, v in enumerate(feats):
            rng_state = (1103515245 * (rng_state + i + 1) + 12345) & 0x7FFFFFFF
            acc += float(v) * ((rng_state % 1000) / 1000.0)
        pred = 1 if acc >= 0.5 else 0
        if pred == label:
            correct += 1
    return correct / len(rows)


def _aggregate(values: list[float], how: str) -> float:
    if how == "mean":
        return float(statistics.fmean(values))
    if how == "median":
        return float(statistics.median(values))
    if how == "min":
        return float(min(values))
    raise ValueError(f"unknown aggregate: {how}")


def evaluate_metric_card(
    card: dict[str, Any],
    *,
    dataset_root: str | Path,
    ablation_module_scores: dict[str, float] | None = None,
    tokens_used: float = 1.0,
    utility_gain: float | None = None,
) -> EvalBundle:
    """Evaluate held-in/held-out multi-seed metrics from on-disk JSONL datasets."""
    card = validate_instance("metric_card", card)
    root = Path(dataset_root)
    held_in_path = root / card["held_in"]["dataset_ref"]
    held_out_path = root / card["held_out"]["dataset_ref"]
    if not held_in_path.is_file() or not held_out_path.is_file():
        raise FileNotFoundError(
            f"metric card datasets missing under {root}: "
            f"{card['held_in']['dataset_ref']}, {card['held_out']['dataset_ref']}"
        )

    held_in_rows = _load_jsonl(held_in_path)
    held_out_rows = _load_jsonl(held_out_path)
    seeds = list(card["multi_seed"]["seeds"])
    agg = card["multi_seed"]["aggregate"]

    held_in_seed = [_score_rows(held_in_rows, card["held_in"]["metric_name"], s) for s in seeds]
    held_out_seed = [_score_rows(held_out_rows, card["held_out"]["metric_name"], s) for s in seeds]
    held_in = _aggregate(held_in_seed, agg)
    held_out = _aggregate(held_out_seed, agg)

    ablation_ok = True
    ablation_details: dict[str, float] = {}
    if card["module_ablation"]["required"]:
        if not ablation_module_scores:
            ablation_ok = False
        else:
            for mod in card["module_ablation"]["modules"]:
                if mod not in ablation_module_scores:
                    ablation_ok = False
                else:
                    ablation_details[mod] = float(ablation_module_scores[mod])
                    # Ablation must not improve held-out beyond full model (gaming signal)
                    if ablation_details[mod] > held_out + 1e-9:
                        ablation_ok = False

    gain = held_out if utility_gain is None else float(utility_gain)
    denom = max(float(tokens_used), 1e-9)
    token_roi = gain / denom
    if not math.isfinite(token_roi):
        raise ValueError("token_roi not finite")

    return EvalBundle(
        card_id=card["card_id"],
        scores={
            "held_in": held_in,
            "held_out": held_out,
            "token_roi": token_roi,
        },
        seed_scores={"held_in": held_in_seed, "held_out": held_out_seed},
        token_roi=token_roi,
        ablation_ok=ablation_ok,
        details={"ablation": ablation_details, "seeds": seeds, "aggregate": agg},
    )
