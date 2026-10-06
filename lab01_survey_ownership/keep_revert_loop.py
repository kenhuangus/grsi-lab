"""Minimal evolutionary keep/revert loop (no real training)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from rsi_core.lineage import close_lineage, open_lineage
from rsi_core.types import LineageId


ScoreFn = Callable[[dict], float]


@dataclass
class LoopState:
    """State of a single keep/revert lineage."""

    lineage_id: LineageId
    generation: int = 0
    best_score: float = float("-inf")
    best_candidate: dict | None = None
    history: list[dict] = field(default_factory=list)


def run_keep_revert(
    candidates: list[dict],
    score_fn: ScoreFn,
    *,
    min_delta: float = 0.0,
) -> LoopState:
    """Propose candidates in order; keep if score improves by ``min_delta``.

    Each candidate dict should include at least ``{"id": ..., "payload": ...}``.
    Closing decision is ``keep`` if any candidate was retained, else ``revert``.
    """
    record = open_lineage(lab="lab01_keep_revert")
    state = LoopState(lineage_id=record.lineage_id)

    for cand in candidates:
        state.generation += 1
        score = float(score_fn(cand))
        entry = {"candidate": cand, "score": score, "decision": "revert"}
        if score > state.best_score + min_delta:
            state.best_score = score
            state.best_candidate = cand
            entry["decision"] = "keep"
        state.history.append(entry)

    if state.best_candidate is None:
        close_lineage(state.lineage_id, "revert", reason="no improvement")
    else:
        close_lineage(state.lineage_id, "keep", reason="score improved")
    return state
