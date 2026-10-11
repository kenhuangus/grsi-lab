"""Shim — canonical implementation lives in ``labs.ch10_ecosystem``."""

from labs.ch10_ecosystem.failure_atlas import (
    DEFAULT_SEED,
    LOOP_STEPS,
    by_loop_step,
    index_by_step,
    load_entries,
)

__all__ = [
    "DEFAULT_SEED",
    "LOOP_STEPS",
    "by_loop_step",
    "index_by_step",
    "load_entries",
]
