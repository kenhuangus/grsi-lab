"""Planner / implementer proposal engine producing candidate_diff envelopes."""

from __future__ import annotations

from typing import Any, Literal

from rsi_core.lineage import open_lineage
from rsi_core.ownership import reject_locked_writes
from rsi_core.schemas_load import validate_instance
from rsi_core.types import Surface


ProposerRole = Literal["planner", "implementer", "in_harness_verifier"]


def build_proposal(
    *,
    surface: Surface | str,
    hypothesis: str,
    metric: str,
    paths: list[str],
    summary: str,
    rollback_unit: str,
    snapshot_ref: str,
    proposer_role: ProposerRole,
    ownership_manifest: dict[str, Any] | None = None,
    lineage_id: str | None = None,
) -> dict[str, Any]:
    """Build and validate a candidate_diff envelope.

    Rejects before return if paths touch locked ownership prefixes.
    """
    if lineage_id is None:
        lineage_id = open_lineage(role=proposer_role).lineage_id

    if ownership_manifest is not None:
        reject_locked_writes(paths, ownership_manifest)

    if not hypothesis.strip() or not metric.strip():
        raise ValueError("Untestable proposal: hypothesis and metric required")
    if not paths:
        raise ValueError("Unscoped proposal: diff.paths must be non-empty")

    surface_value = surface.value if isinstance(surface, Surface) else surface
    envelope: dict[str, Any] = {
        "lineage_id": lineage_id,
        "surface": surface_value,
        "hypothesis": hypothesis,
        "metric": metric,
        "rollback": {"unit": rollback_unit, "snapshot_ref": snapshot_ref},
        "diff": {"paths": paths, "summary": summary},
        "proposer_role": proposer_role,
    }
    return validate_instance("candidate_diff", envelope)


def plan_then_implement(
    plan_hypothesis: str,
    implement_summary: str,
    *,
    metric: str,
    paths: list[str],
    rollback_unit: str,
    snapshot_ref: str,
    ownership_manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Emit a planner proposal then an implementer proposal sharing lineage."""
    planner = build_proposal(
        surface=Surface.MODEL,
        hypothesis=plan_hypothesis,
        metric=metric,
        paths=paths,
        summary="planner scope",
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        proposer_role="planner",
        ownership_manifest=ownership_manifest,
    )
    implementer = build_proposal(
        surface=Surface.MODEL,
        hypothesis=plan_hypothesis,
        metric=metric,
        paths=paths,
        summary=implement_summary,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        proposer_role="implementer",
        ownership_manifest=ownership_manifest,
        lineage_id=planner["lineage_id"],
    )
    return planner, implementer
