"""Lab 02 (legacy) — re-exports Chapter 3 proposals + Chapter 4 model surface."""

from labs.ch03_proposals.planner import plan_then_implement
from labs.ch03_proposals.reject_gates import build_proposal
from labs.ch04_model_surface.adapter_package import (
    AdapterPackage,
    LoRAEnvelope,
    make_adapter_candidate,
)
from labs.ch04_model_surface.forgetting_gate import ForgettingGateResult, forgetting_gate

__all__ = [
    "AdapterPackage",
    "ForgettingGateResult",
    "LoRAEnvelope",
    "build_proposal",
    "forgetting_gate",
    "make_adapter_candidate",
    "plan_then_implement",
]
