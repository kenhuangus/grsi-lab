"""Module ablation rows for harness keep decisions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from labs.ch06_orchestration.harness_store import HarnessStore

ScoreFn = Callable[[HarnessStore], float]


@dataclass
class AblationRow:
    module_id: str
    full_score: float
    ablated_score: float
    delta: float
    attributed: bool
    notes: str = ""


@dataclass
class AblationReport:
    passed: bool
    reason: str
    rows: list[AblationRow] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def run_module_ablation(
    store: HarnessStore,
    module_ids: list[str],
    score_fn: ScoreFn,
    *,
    min_attributable_delta: float = 0.01,
    require_all: bool = True,
) -> AblationReport:
    """Ablate each module by rolling back to its snapshot and re-scoring.

    Attribution passes when restoring the prior snapshot moves the score by at
    least ``min_attributable_delta``. Modules without snapshots refuse.
    """
    if not module_ids:
        return AblationReport(False, "no modules listed for ablation")

    rows: list[AblationRow] = []
    full_score = float(score_fn(store))

    for module_id in module_ids:
        if module_id not in store.modules:
            return AblationReport(False, f"unknown module for ablation: {module_id}", rows)
        if module_id not in store.snapshots:
            return AblationReport(
                False,
                f"missing snapshot for ablation: {module_id}",
                rows,
            )

        current = dict(store.modules[module_id])
        store.rollback(module_id)
        ablated_score = float(score_fn(store))
        # restore candidate for next ablation
        store.modules[module_id] = current
        delta = full_score - ablated_score
        attributed = abs(delta) >= min_attributable_delta
        rows.append(
            AblationRow(
                module_id=module_id,
                full_score=full_score,
                ablated_score=ablated_score,
                delta=delta,
                attributed=attributed,
                notes="gain attributable" if attributed else "gain not attributable",
            )
        )

    attributed_ids = [r.module_id for r in rows if r.attributed]
    if require_all and len(attributed_ids) != len(rows):
        return AblationReport(
            False,
            "ablation failed: one or more modules not attributable",
            rows,
            details={"attributed": attributed_ids},
        )
    if not attributed_ids:
        return AblationReport(
            False,
            "ablation failed: no module attributed the score delta",
            rows,
        )
    return AblationReport(
        True,
        "ablation cleared",
        rows,
        details={"attributed": attributed_ids, "full_score": full_score},
    )
