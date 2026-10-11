"""Lab 05 (legacy) — re-exports Chapter 9 promotion + Chapter 10 ecosystem."""

from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.promotion_gateway import PromotionError, promote, validate_token
from labs.ch10_ecosystem.boundary_proxy import BoundaryProxy, EgressDenied
from labs.ch10_ecosystem.failure_atlas import (
    DEFAULT_SEED,
    LOOP_STEPS,
    by_loop_step,
    index_by_step,
    load_entries,
)
from labs.ch10_ecosystem.kill_rollback import KillSwitch, kill_and_rollback
from labs.ch10_ecosystem.publication_gate import PublicationError, PublicationGate

__all__ = [
    "BoundaryProxy",
    "DEFAULT_SEED",
    "EgressDenied",
    "KillSwitch",
    "LOOP_STEPS",
    "PublicationError",
    "PublicationGate",
    "PromotionError",
    "by_loop_step",
    "index_by_step",
    "kill_and_rollback",
    "load_entries",
    "promote",
    "run_frozen_policy_scan",
    "validate_token",
]
