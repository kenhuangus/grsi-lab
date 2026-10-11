"""Refuse gate: score_fn must not be owned by the candidate payload."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


def refuse_if_scorer_in_payload(candidate: dict[str, Any]) -> None:
    """Fail closed when a candidate tries to ship or replace the scorer."""
    payload = candidate.get("payload") or {}
    if "score_fn" in candidate or "score_fn" in payload:
        raise PermissionError("refuse: candidate must not own score_fn")

def safe_score(candidate: dict[str, Any], score_fn: Callable[[dict], float]) -> float:
    refuse_if_scorer_in_payload(candidate)
    return float(score_fn(candidate))
