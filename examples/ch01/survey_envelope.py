"""Minimal proposal envelope fields used in Chapter 1 survey exercises."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rsi_core.types import Surface


@dataclass(frozen=True)
class SurveyEnvelope:
    proposal_id: str
    surface: Surface
    target_paths: list[str]
    eval_hook: str
    rollback_unit: str
    diff_payload: dict[str, Any] = field(default_factory=dict)

def require_envelope_fields(env: SurveyEnvelope) -> None:
    if not env.target_paths or not env.eval_hook or not env.rollback_unit:
        raise ValueError("envelope missing paths, eval_hook, or rollback_unit")
