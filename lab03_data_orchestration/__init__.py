"""Lab 03 (legacy) — re-exports Chapter 5 data + Chapter 6 orchestration."""

from labs.ch05_data_memory.admit_experience import (
    AdmissionPolicy,
    AdmissionResult,
    admit_experience,
    verify_experience_admission,
)
from labs.ch06_orchestration.harness_store import HarnessStore, ModuleSnapshot, module_hash

__all__ = [
    "AdmissionPolicy",
    "AdmissionResult",
    "HarnessStore",
    "ModuleSnapshot",
    "admit_experience",
    "module_hash",
    "verify_experience_admission",
]
