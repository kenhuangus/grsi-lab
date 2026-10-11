"""Shim — canonical implementation lives in ``labs.ch05_data_memory.admit_experience``."""

from labs.ch05_data_memory.admit_experience import (  # noqa: F401
    AdmissionPolicy,
    AdmissionResult,
    admit_experience,
    verify_experience_admission,
)

__all__ = [
    "AdmissionPolicy",
    "AdmissionResult",
    "admit_experience",
    "verify_experience_admission",
]
