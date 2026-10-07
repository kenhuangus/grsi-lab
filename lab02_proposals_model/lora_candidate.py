"""Stub LoRA candidate envelope and forgetting gate (no real training)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoRAEnvelope:
    """Stub adapter candidate — metadata only, no weights."""

    lineage_id: str
    base_model_ref: str
    adapter_name: str
    rank: int
    target_modules: list[str] = field(default_factory=list)
    forgetting_gate_threshold: float = 0.05
    prior_task_scores: dict[str, float] = field(default_factory=dict)
    notes: str = "stub — no GPU training"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "base_model_ref": self.base_model_ref,
            "adapter_name": self.adapter_name,
            "rank": self.rank,
            "target_modules": list(self.target_modules),
            "forgetting_gate_threshold": self.forgetting_gate_threshold,
            "prior_task_scores": dict(self.prior_task_scores),
            "notes": self.notes,
        }


@dataclass
class ForgettingGateResult:
    """Outcome of the stub forgetting gate."""

    passed: bool
    regressions: dict[str, float]
    message: str


def forgetting_gate(
    envelope: LoRAEnvelope,
    post_task_scores: dict[str, float],
) -> ForgettingGateResult:
    """Reject candidate if any prior task regresses beyond the threshold.

    Compares ``post_task_scores`` to ``envelope.prior_task_scores``. A drop
    larger than ``forgetting_gate_threshold`` fails the gate.
    """
    regressions: dict[str, float] = {}
    missing: list[str] = []
    for task, prior in envelope.prior_task_scores.items():
        post = post_task_scores.get(task)
        if post is None:
            missing.append(task)
            continue
        drop = prior - post
        if drop > envelope.forgetting_gate_threshold:
            regressions[task] = drop

    if missing:
        return ForgettingGateResult(
            passed=False,
            regressions=regressions,
            message=(
                "forgetting gate failed: missing post scores for "
                + ", ".join(sorted(missing))
            ),
        )
    if regressions:
        return ForgettingGateResult(
            passed=False,
            regressions=regressions,
            message="forgetting gate failed: prior-task regression",
        )
    return ForgettingGateResult(
        passed=True,
        regressions={},
        message="forgetting gate passed",
    )


def make_stub_lora(
    lineage_id: str,
    *,
    base_model_ref: str = "stub-base",
    adapter_name: str = "candidate-adapter",
    rank: int = 8,
) -> LoRAEnvelope:
    """Factory for a stub LoRA envelope used in labs/demo."""
    return LoRAEnvelope(
        lineage_id=lineage_id,
        base_model_ref=base_model_ref,
        adapter_name=adapter_name,
        rank=rank,
        target_modules=["q_proj", "v_proj"],
        prior_task_scores={"task_a": 0.80, "task_b": 0.75},
    )
