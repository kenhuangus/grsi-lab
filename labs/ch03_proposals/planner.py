"""Planner role — scopes surface, metric, and paths under one lineage."""

from __future__ import annotations

from typing import Any

from labs.ch03_proposals.reject_gates import build_proposal
from rsi_core.types import Surface


def plan_proposal(
    *,
    surface: Surface | str,
    hypothesis: str,
    metric: str,
    paths: list[str],
    rollback_unit: str,
    snapshot_ref: str,
    ownership_manifest: dict[str, Any] | None = None,
    summary: str = "planner scope",
    require_manifest: bool = True,
) -> dict[str, Any]:
    """Emit a planner candidate_diff that opens lineage and declares scope."""
    return build_proposal(
        surface=surface,
        hypothesis=hypothesis,
        metric=metric,
        paths=paths,
        summary=summary,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        proposer_role="planner",
        ownership_manifest=ownership_manifest,
        require_manifest=require_manifest,
    )


def plan_then_implement(
    plan_hypothesis: str,
    implement_summary: str,
    *,
    metric: str,
    paths: list[str],
    rollback_unit: str,
    snapshot_ref: str,
    ownership_manifest: dict[str, Any] | None = None,
    surface: Surface | str = Surface.MODEL,
    require_manifest: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Emit planner then implementer envelopes sharing one lineage UUID."""
    from labs.ch03_proposals.implementer import implement_proposal

    planner = plan_proposal(
        surface=surface,
        hypothesis=plan_hypothesis,
        metric=metric,
        paths=paths,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        ownership_manifest=ownership_manifest,
        require_manifest=require_manifest,
    )
    implementer = implement_proposal(
        surface=surface,
        hypothesis=plan_hypothesis,
        metric=metric,
        paths=paths,
        summary=implement_summary,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        ownership_manifest=ownership_manifest,
        lineage_id=planner["lineage_id"],
        require_manifest=require_manifest,
        approved_paths=list(paths),
    )
    return planner, implementer
