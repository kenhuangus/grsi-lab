"""Implementer role — concrete diff summary under planner-opened lineage."""

from __future__ import annotations

from typing import Any

from labs.ch03_proposals.reject_gates import ProposalRejectError, build_proposal
from rsi_core.types import Surface


def implement_proposal(
    *,
    surface: Surface | str,
    hypothesis: str,
    metric: str,
    paths: list[str],
    summary: str,
    rollback_unit: str,
    snapshot_ref: str,
    ownership_manifest: dict[str, Any] | None = None,
    lineage_id: str | None = None,
    require_manifest: bool = True,
    approved_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Emit an implementer candidate_diff.

    When ``approved_paths`` is set (planner scope), any path outside that set is
    refused as unscoped scope expansion.
    """
    if approved_paths is not None:
        approved = set(approved_paths)
        extra = [p for p in paths if p not in approved]
        if extra:
            raise ProposalRejectError(
                "unscoped",
                "Unscoped proposal: implementer paths exceed planner scope: "
                + ", ".join(extra),
            )

    return build_proposal(
        surface=surface,
        hypothesis=hypothesis,
        metric=metric,
        paths=paths,
        summary=summary,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        proposer_role="implementer",
        ownership_manifest=ownership_manifest,
        lineage_id=lineage_id,
        require_manifest=require_manifest,
    )
