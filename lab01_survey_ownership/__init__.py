"""Lab 01 (legacy) — re-exports Chapter 1 examples + Chapter 2 ownership."""

from examples.ch01.keep_revert_loop import LoopState, run_keep_revert
from examples.ch01.taxonomy import (
    Evaluability,
    Mutability,
    TaxonomyCell,
    classify,
)
from labs.ch02_ownership.manifest import (
    REQUIRED_COMPONENT_FIELDS,
    validate_manifest_file,
    validate_modularity,
)

__all__ = [
    "REQUIRED_COMPONENT_FIELDS",
    "Evaluability",
    "LoopState",
    "Mutability",
    "TaxonomyCell",
    "classify",
    "run_keep_revert",
    "validate_manifest_file",
    "validate_modularity",
]
