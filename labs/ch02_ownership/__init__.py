"""Chapter 2 lab — ownership manifests, locked writes, freeze gate, blast radius."""

from labs.ch02_ownership.blast_radius import (
    BlastRadiusAssessment,
    assess_blast_radius,
    undeclared_cross_surface,
)
from labs.ch02_ownership.freeze_gate import (
    FreezeGateResult,
    FreezeStatus,
    run_freeze_gate,
)
from labs.ch02_ownership.manifest import (
    REQUIRED_COMPONENT_FIELDS,
    validate_manifest_file,
    validate_modularity,
)
from labs.ch02_ownership.reject_locked_writes import (
    RejectReport,
    assert_paths_writable,
    reject_locked_writes,
)

__all__ = [
    "REQUIRED_COMPONENT_FIELDS",
    "BlastRadiusAssessment",
    "FreezeGateResult",
    "FreezeStatus",
    "RejectReport",
    "assess_blast_radius",
    "assert_paths_writable",
    "reject_locked_writes",
    "run_freeze_gate",
    "undeclared_cross_surface",
    "validate_manifest_file",
    "validate_modularity",
]
