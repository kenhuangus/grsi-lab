"""Preference / post-training recipe contracts (SFT, DPO, RLAIF)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

RecipeKind = Literal["sft", "dpo", "rlaif"]


@dataclass(frozen=True)
class RecipeContract:
    """Frozen recipe fields that must not drift mid-run without a new lineage."""

    lineage_id: str
    kind: RecipeKind
    data_mix_id: str
    loss_name: str
    schedule: str
    stop_rule: str
    preference_source: str | None = None
    judge_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "lineage_id": self.lineage_id,
            "kind": self.kind,
            "data_mix_id": self.data_mix_id,
            "loss_name": self.loss_name,
            "schedule": self.schedule,
            "stop_rule": self.stop_rule,
        }
        if self.preference_source is not None:
            payload["preference_source"] = self.preference_source
        if self.judge_ref is not None:
            payload["judge_ref"] = self.judge_ref
        return payload


class RecipeContractError(ValueError):
    """Raised when a recipe is incomplete or drifts without a new envelope."""


def _require_nonempty(name: str, value: str) -> str:
    if not value or not value.strip():
        raise RecipeContractError(f"unscoped recipe: {name} required")
    return value.strip()


def build_recipe_contract(
    *,
    lineage_id: str,
    kind: RecipeKind,
    data_mix_id: str,
    loss_name: str,
    schedule: str,
    stop_rule: str,
    preference_source: str | None = None,
    judge_ref: str | None = None,
) -> RecipeContract:
    """Build a recipe contract; preference kinds require judge + preference source."""
    kind_norm: RecipeKind = kind  # type: ignore[assignment]
    if kind_norm not in {"sft", "dpo", "rlaif"}:
        raise RecipeContractError(f"unknown recipe kind: {kind}")
    contract = RecipeContract(
        lineage_id=_require_nonempty("lineage_id", lineage_id),
        kind=kind_norm,
        data_mix_id=_require_nonempty("data_mix_id", data_mix_id),
        loss_name=_require_nonempty("loss_name", loss_name),
        schedule=_require_nonempty("schedule", schedule),
        stop_rule=_require_nonempty("stop_rule", stop_rule),
        preference_source=preference_source.strip() if preference_source else None,
        judge_ref=judge_ref.strip() if judge_ref else None,
    )
    if contract.kind in {"dpo", "rlaif"}:
        if not contract.preference_source:
            raise RecipeContractError(
                f"unscoped recipe: preference_source required for {contract.kind}"
            )
        if not contract.judge_ref:
            raise RecipeContractError(
                f"unscoped recipe: judge_ref required for {contract.kind}"
            )
    return contract


def recipe_canonical_hash(contract: RecipeContract) -> str:
    """SHA-256 of canonical JSON form (proposal-time pin)."""
    blob = json.dumps(contract.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assert_recipe_unchanged(
    pinned: RecipeContract,
    observed: RecipeContract,
) -> None:
    """Refuse mid-run recipe drift (must open a new lineage instead)."""
    if recipe_canonical_hash(pinned) != recipe_canonical_hash(observed):
        raise RecipeContractError(
            "recipe drift without new lineage: "
            f"pinned={recipe_canonical_hash(pinned)[:12]} "
            f"observed={recipe_canonical_hash(observed)[:12]}"
        )
    if pinned.lineage_id != observed.lineage_id:
        raise RecipeContractError(
            f"recipe lineage mismatch: pinned={pinned.lineage_id} "
            f"observed={observed.lineage_id}"
        )
