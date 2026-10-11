"""Train-job records that pin adapter, recipe, and metric-card identity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from labs.ch04_model_surface.adapter_package import AdapterPackage
from labs.ch04_model_surface.recipe_contract import RecipeContract, recipe_canonical_hash

JobStatus = Literal["queued", "running", "completed", "failed", "refused"]


@dataclass
class TrainJobRecord:
    """Local train-job record (no GPU): pins digests for audit and rollback."""

    job_id: str
    lineage_id: str
    adapter_dir: str
    adapter_weights_sha256: str
    adapter_config_sha256: str
    base_model_ref: str
    recipe_hash: str
    metric_card_id: str
    metric_card_sha256: str
    sandbox_profile_id: str
    status: JobStatus = "queued"
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "lineage_id": self.lineage_id,
            "adapter_dir": self.adapter_dir,
            "adapter_weights_sha256": self.adapter_weights_sha256,
            "adapter_config_sha256": self.adapter_config_sha256,
            "base_model_ref": self.base_model_ref,
            "recipe_hash": self.recipe_hash,
            "metric_card_id": self.metric_card_id,
            "metric_card_sha256": self.metric_card_sha256,
            "sandbox_profile_id": self.sandbox_profile_id,
            "status": self.status,
            "created_at": self.created_at,
            "notes": self.notes,
        }


class TrainJobError(ValueError):
    """Raised when a train job cannot be opened under contract pins."""


def _job_id(lineage_id: str, weights_sha: str, recipe_hash: str) -> str:
    material = f"{lineage_id}:{weights_sha}:{recipe_hash}".encode()
    return hashlib.sha256(material).hexdigest()[:32]


def open_train_job(
    *,
    package: AdapterPackage,
    recipe: RecipeContract,
    metric_card_id: str,
    metric_card_sha256: str,
    sandbox_profile_id: str,
) -> TrainJobRecord:
    """Open a train-job record only when lineage and pins are complete."""
    if package.lineage_id != recipe.lineage_id:
        raise TrainJobError(
            f"lineage mismatch: adapter={package.lineage_id} recipe={recipe.lineage_id}"
        )
    if not metric_card_id.strip() or not metric_card_sha256.strip():
        raise TrainJobError("metric card id and sha256 required before train")
    if not sandbox_profile_id.strip():
        raise TrainJobError("sandbox_profile_id required; proposer cannot omit jail")
    if len(metric_card_sha256) < 32:
        raise TrainJobError("metric_card_sha256 looks truncated; refuse train open")

    recipe_hash = recipe_canonical_hash(recipe)
    job_id = _job_id(package.lineage_id, package.weights_sha256, recipe_hash)
    return TrainJobRecord(
        job_id=job_id,
        lineage_id=package.lineage_id,
        adapter_dir=package.adapter_dir,
        adapter_weights_sha256=package.weights_sha256,
        adapter_config_sha256=package.config_sha256,
        base_model_ref=package.base_model_ref,
        recipe_hash=recipe_hash,
        metric_card_id=metric_card_id.strip(),
        metric_card_sha256=metric_card_sha256.strip(),
        sandbox_profile_id=sandbox_profile_id.strip(),
        status="queued",
        notes="train job pinned; no GPU required for lab record",
    )


def refuse_train_without_pins(
    *,
    package: AdapterPackage | None,
    recipe: RecipeContract | None,
    metric_card_id: str | None,
    metric_card_sha256: str | None,
    sandbox_profile_id: str | None,
) -> TrainJobRecord:
    """Explicit refuse helper when callers omit required pins."""
    missing: list[str] = []
    if package is None:
        missing.append("adapter_package")
    if recipe is None:
        missing.append("recipe_contract")
    if not metric_card_id:
        missing.append("metric_card_id")
    if not metric_card_sha256:
        missing.append("metric_card_sha256")
    if not sandbox_profile_id:
        missing.append("sandbox_profile_id")
    raise TrainJobError(
        "train job refused: missing pins: " + ", ".join(missing)
    )


def mark_completed(record: TrainJobRecord) -> TrainJobRecord:
    """Mark a queued/running job completed (lab bookkeeping only)."""
    if record.status == "refused":
        raise TrainJobError("cannot complete a refused train job")
    record.status = "completed"
    return record


def dump_train_job(record: TrainJobRecord, path: str) -> None:
    """Write the train-job record as canonical JSON."""
    from pathlib import Path

    Path(path).write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
