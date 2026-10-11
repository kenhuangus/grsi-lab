"""Cheapest-surface escalation gate before opening surface=model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from rsi_core.lineage import LineageStatus, get_lineage
from rsi_core.types import Surface, parse_lineage_id

CheaperSurface = Literal["orchestration", "data"]
_CLOSED_STATUSES = frozenset(
    {LineageStatus.KEEP, LineageStatus.REVERT, LineageStatus.REJECT}
)


@dataclass(frozen=True)
class CheaperAttempt:
    """Evidence that a cheaper surface was tried under the same metric card."""

    lineage_id: str
    surface: CheaperSurface
    metric: str
    outcome: Literal["failed_min_delta", "ownership_blocked", "reverted"]
    notes: str = ""


@dataclass
class EscalationDecision:
    """Whether a model-surface proposal may open."""

    allowed: bool
    refusals: list[str] = field(default_factory=list)
    attempts: list[CheaperAttempt] = field(default_factory=list)
    message: str = ""


def _resolve_registered_lineage(attempt: CheaperAttempt, *, metric: str) -> list[str]:
    """Refuse self-attested lineage: must exist closed in the Ch3/rsi_core registry."""
    errors: list[str] = []
    try:
        lid = parse_lineage_id(attempt.lineage_id)
    except ValueError:
        return [f"invalid cheaper-surface lineage_id: {attempt.lineage_id!r}"]

    try:
        record = get_lineage(lid)
    except KeyError:
        return [
            f"cheaper-surface lineage not in registry (self-attested refused): {lid}"
        ]

    if record.status not in _CLOSED_STATUSES:
        errors.append(
            f"cheaper-surface lineage {lid} is not closed "
            f"(status={record.status.value})"
        )

    registered_metric = str(record.metadata.get("metric", "")).strip()
    if not registered_metric:
        errors.append(f"cheaper-surface lineage {lid} missing registry metric metadata")
    elif registered_metric != metric.strip():
        errors.append(
            f"cheaper-surface lineage {lid} metric {registered_metric!r} "
            f"!= model metric {metric!r}"
        )

    registered_surface = str(record.metadata.get("surface", "")).strip()
    if registered_surface and registered_surface != attempt.surface:
        errors.append(
            f"cheaper-surface lineage {lid} surface {registered_surface!r} "
            f"!= attempt surface {attempt.surface!r}"
        )
    return errors


def validate_cheaper_attempt(attempt: CheaperAttempt, *, metric: str) -> list[str]:
    """Return validation errors for one cheaper-surface attempt record."""
    errors: list[str] = []
    try:
        parse_lineage_id(attempt.lineage_id)
    except ValueError:
        errors.append(f"invalid cheaper-surface lineage_id: {attempt.lineage_id!r}")
    if attempt.surface not in {"orchestration", "data"}:
        errors.append(f"surface not cheaper than model: {attempt.surface}")
    if attempt.metric.strip() != metric.strip():
        errors.append(
            f"cheaper attempt metric {attempt.metric!r} != model metric {metric!r}"
        )
    if attempt.outcome not in {"failed_min_delta", "ownership_blocked", "reverted"}:
        errors.append(f"invalid cheaper-surface outcome: {attempt.outcome}")
    if not errors:
        errors.extend(_resolve_registered_lineage(attempt, metric=metric))
    return errors


def require_cheapest_surface(
    *,
    metric: str,
    failure_statement: str,
    cheaper_attempts: list[CheaperAttempt],
    harness_candidates: list[str] | None = None,
    experience_candidates: list[str] | None = None,
    # Back-compat kwargs: treated as empty lists when False, refused when True without lists.
    harness_candidates_listed: bool | None = None,
    experience_candidates_listed: bool | None = None,
) -> EscalationDecision:
    """Refuse model-surface open unless cheaper surfaces were evidenced.

    Checklist (Chapter 4):
    1. Failure stated in metric-card terms.
    2. Non-empty harness or experience candidate lists.
    3. Cheaper attempts cited by *registered closed* lineage under the same metric.
    4. Only then may surface=model open.
    """
    refusals: list[str] = []
    if not failure_statement.strip():
        refusals.append("failure statement empty; state the failure in metric-card terms")
    if metric.strip() not in failure_statement and metric.strip():
        if metric.replace("_", " ") not in failure_statement.lower():
            refusals.append(
                f"failure statement must name metric {metric!r} (not model brand terms)"
            )

    harness = list(harness_candidates or [])
    experience = list(experience_candidates or [])
    if harness_candidates is None and harness_candidates_listed is True:
        refusals.append(
            "harness_candidates_listed is not evidence; pass non-empty harness_candidates"
        )
    if experience_candidates is None and experience_candidates_listed is True:
        refusals.append(
            "experience_candidates_listed is not evidence; "
            "pass non-empty experience_candidates"
        )
    harness = [c for c in harness if str(c).strip()]
    experience = [c for c in experience if str(c).strip()]
    if not harness and not experience:
        refusals.append(
            "list non-empty harness_candidates or experience_candidates "
            "that could address the same failure"
        )

    if not cheaper_attempts:
        refusals.append(
            "no cheaper-surface lineage evidence; "
            "'we tried a prompt edit last month' is not evidence"
        )

    valid_attempts: list[CheaperAttempt] = []
    for attempt in cheaper_attempts:
        errors = validate_cheaper_attempt(attempt, metric=metric)
        if errors:
            refusals.extend(errors)
        else:
            valid_attempts.append(attempt)

    if cheaper_attempts and not valid_attempts:
        refusals.append("no valid cheaper-surface attempts after validation")

    if refusals:
        return EscalationDecision(
            allowed=False,
            refusals=refusals,
            attempts=list(cheaper_attempts),
            message="cheapest-surface gate refused model open: " + "; ".join(refusals),
        )

    return EscalationDecision(
        allowed=True,
        refusals=[],
        attempts=valid_attempts,
        message=(
            f"cheapest-surface gate allowed model open after "
            f"{len(valid_attempts)} cheaper attempt(s)"
        ),
    )


def escalation_hypothesis_prefix(decision: EscalationDecision) -> str:
    """Format lineage references for inclusion in a model proposal hypothesis."""
    if not decision.allowed:
        raise ValueError("cannot format hypothesis prefix for refused escalation")
    parts = [
        f"Lineage {a.lineage_id} {a.outcome} on metric {a.metric} under {a.surface}"
        for a in decision.attempts
    ]
    return "Cheaper-surface evidence: " + "; ".join(parts) + "."


def assert_model_surface(envelope: dict[str, Any]) -> None:
    """Refuse envelopes that claim model packaging without surface=model."""
    surface = envelope.get("surface")
    if surface != Surface.MODEL.value:
        raise ValueError(
            f"adapter packaging requires surface=model, got {surface!r}"
        )
