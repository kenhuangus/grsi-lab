"""Pre-execution proposal reject gates: untestable, unscoped, locked_path."""

from __future__ import annotations

from typing import Any, Literal

from labs.ch02_ownership.reject_locked_writes import assert_paths_writable
from rsi_core.lineage import open_lineage
from rsi_core.schemas_load import validate_instance
from rsi_core.types import LockedPathError, Surface

ProposerRole = Literal["planner", "implementer", "in_harness_verifier"]
RejectClass = Literal["untestable", "unscoped", "locked_path"]


class ProposalRejectError(ValueError):
    """Raised when a proposal fails a pre-execution reject gate."""

    def __init__(self, reject_class: RejectClass, message: str) -> None:
        self.reject_class = reject_class
        super().__init__(message)


def check_untestable(hypothesis: str, metric: str) -> None:
    """Refuse proposals that cannot be bound to a metric card later."""
    if not hypothesis.strip() or not metric.strip():
        raise ProposalRejectError(
            "untestable",
            "Untestable proposal: hypothesis and metric required",
        )


def check_unscoped(
    paths: list[str],
    *,
    rollback_unit: str,
    snapshot_ref: str,
    summary: str,
) -> None:
    """Refuse proposals without concrete scope or rollback identity."""
    if not paths:
        raise ProposalRejectError(
            "unscoped",
            "Unscoped proposal: diff.paths must be non-empty",
        )
    if not rollback_unit.strip() or not snapshot_ref.strip():
        raise ProposalRejectError(
            "unscoped",
            "Unscoped proposal: rollback.unit and snapshot_ref required",
        )
    if not summary.strip():
        raise ProposalRejectError(
            "unscoped",
            "Unscoped proposal: diff.summary required",
        )


def check_locked_paths(
    paths: list[str],
    ownership_manifest: dict[str, Any],
) -> None:
    """Refuse locked, undeclared, or parent-traversal writes (Ch2 declared+locked)."""
    assert_paths_writable(paths, ownership_manifest, require_declared=True)


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
    require_manifest: bool = True,
) -> dict[str, Any]:
    """Build and validate a candidate_diff envelope under refuse-first gates.

    Order: open/reuse lineage -> locked/undeclared paths -> untestable -> unscoped -> schema.
    Lineage opens first so refused proposals still have an identity for telemetry.

    When ``require_manifest`` is True (default), omitting ``ownership_manifest`` is
    refused as unscoped. When False, ``None`` skips the ownership check (compat
    only); production configs must always supply a staging manifest.
    """
    if lineage_id is None:
        lineage_id = open_lineage(role=proposer_role).lineage_id

    if require_manifest and ownership_manifest is None:
        raise ProposalRejectError(
            "unscoped",
            "Unscoped proposal: ownership_manifest is required",
        )
    if ownership_manifest is not None:
        try:
            check_locked_paths(paths, ownership_manifest)
        except LockedPathError:
            raise

    check_untestable(hypothesis, metric)
    check_unscoped(
        paths,
        rollback_unit=rollback_unit,
        snapshot_ref=snapshot_ref,
        summary=summary,
    )

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
