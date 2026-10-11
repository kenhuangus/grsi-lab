"""Compatibility shim — adapter package lives in labs.ch04_model_surface."""

from labs.ch04_model_surface.adapter_package import (
    AdapterPackage,
    LoRAEnvelope,
    load_adapter_package,
    load_lora_envelope,
    make_adapter_candidate,
    verify_adapter_artifact,
    write_adapter_artifact,
)
from labs.ch04_model_surface.forgetting_gate import ForgettingGateResult, forgetting_gate

__all__ = [
    "AdapterPackage",
    "ForgettingGateResult",
    "LoRAEnvelope",
    "forgetting_gate",
    "load_adapter_package",
    "load_lora_envelope",
    "make_adapter_candidate",
    "verify_adapter_artifact",
    "write_adapter_artifact",
]
