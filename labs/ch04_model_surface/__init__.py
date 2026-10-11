"""Chapter 4 lab — adapter packages, forgetting gate, cheapest surface, recipes."""

from labs.ch04_model_surface.adapter_package import (
    AdapterPackage,
    LoRAEnvelope,
    make_adapter_candidate,
    verify_adapter_artifact,
    write_adapter_artifact,
)
from labs.ch04_model_surface.cheapest_surface import (
    CheaperAttempt,
    EscalationDecision,
    require_cheapest_surface,
)
from labs.ch04_model_surface.forgetting_gate import ForgettingGateResult, forgetting_gate
from labs.ch04_model_surface.recipe_contract import (
    RecipeContract,
    RecipeContractError,
    assert_recipe_unchanged,
    build_recipe_contract,
    recipe_canonical_hash,
)
from labs.ch04_model_surface.train_job_record import (
    TrainJobError,
    TrainJobRecord,
    open_train_job,
)

__all__ = [
    "AdapterPackage",
    "CheaperAttempt",
    "EscalationDecision",
    "ForgettingGateResult",
    "LoRAEnvelope",
    "RecipeContract",
    "RecipeContractError",
    "TrainJobError",
    "TrainJobRecord",
    "assert_recipe_unchanged",
    "build_recipe_contract",
    "forgetting_gate",
    "make_adapter_candidate",
    "open_train_job",
    "recipe_canonical_hash",
    "require_cheapest_surface",
    "verify_adapter_artifact",
    "write_adapter_artifact",
]
