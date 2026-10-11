"""Surface-tagged blast-radius assessment for Chapter 2 ownership reviews."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from rsi_core.paths import is_under_prefix, normalize_lab_path
from rsi_core.types import Surface

# Relative burden of proof / rollback cost by surface (higher = stricter).
SURFACE_BLAST_RANK: dict[str, int] = {
    Surface.ORCHESTRATION.value: 1,
    Surface.DATA.value: 2,
    Surface.MODEL.value: 3,
    Surface.RESEARCH_PROCESS.value: 4,
    "infrastructure": 5,
}

MINIMUM_EVIDENCE: dict[str, tuple[str, ...]] = {
    Surface.ORCHESTRATION.value: (
        "held_out_task_metric",
        "module_ablation",
        "single_reload_boundary",
    ),
    Surface.DATA.value: (
        "held_out_task_metric",
        "poison_check",
        "collapse_check",
        "diversity_floor",
    ),
    Surface.MODEL.value: (
        "held_out_task_metric",
        "forgetting_gate",
        "cheaper_surface_evidence",
        "overfit_check",
    ),
    Surface.RESEARCH_PROCESS.value: (
        "private_grade_integrity",
        "reward_hack_fixture",
        "held_out_task_metric",
    ),
    "infrastructure": (
        "escape_test",
        "egress_probe",
        "credential_ttl_check",
        "change_control_ticket",
    ),
}


@dataclass
class BlastRadiusAssessment:
    """Blast-radius classification for a candidate path set."""

    surfaces: set[str] = field(default_factory=set)
    primary_surface: str | None = None
    blast_rank: int = 0
    undeclared_cross_surface: bool = False
    infrastructure_touch: bool = False
    required_evidence: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    accepted: bool = False
    message: str = ""


def _surface_for_path(path: str, manifest: dict[str, Any]) -> str | None:
    """Resolve the surface tag for a path from manifest components."""
    target = normalize_lab_path(path)
    best: tuple[int, str] | None = None
    for comp in manifest.get("components") or []:
        comp_path = normalize_lab_path(str(comp.get("path", "")))
        if not comp_path:
            continue
        if is_under_prefix(target, comp_path) or target == comp_path:
            surface = str(comp.get("surface") or "")
            rank = len(comp_path)
            if best is None or rank > best[0]:
                best = (rank, surface)
    if best is None:
        return None
    return best[1] or None


def undeclared_cross_surface(
    paths: list[str],
    manifest: dict[str, Any],
    *,
    declared_surface: str | None = None,
) -> bool:
    """True when paths resolve to more than one surface, or disagree with declaration."""
    surfaces: set[str] = set()
    for path in paths:
        surface = _surface_for_path(path, manifest)
        if surface:
            surfaces.add(surface)
    if len(surfaces) > 1:
        return True
    if declared_surface and surfaces and declared_surface not in surfaces:
        return True
    return False


def _evidence_present(evidence: Mapping[str, Any] | None, key: str) -> bool:
    """True only for non-boolean artifact refs (path/id string or mapping).

    Bare ``True`` is refused — callers must supply a pointer, not a self-claim.
    """
    if not evidence:
        return False
    value = evidence.get(key)
    if value is None or value is False:
        return False
    if value is True:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        path = value.get("path") or value.get("ref") or value.get("id")
        return bool(str(path).strip()) if path is not None else len(value) > 0
    return bool(value)


def assess_blast_radius(
    paths: list[str],
    manifest: dict[str, Any],
    *,
    declared_surface: str | None = None,
    allow_infrastructure: bool = False,
    evidence: Mapping[str, Any] | None = None,
) -> BlastRadiusAssessment:
    """Classify blast radius and refuse undeclared multi-surface / infra writes.

    Accept path: single declared surface (or single resolved surface) with no
    infrastructure touch (unless explicitly allowed via change control), and
    supplied ``evidence`` covering every ``required_evidence`` key.
    """
    result = BlastRadiusAssessment()
    if not paths:
        result.refusals.append("unscoped: empty path list")
        result.message = "blast radius refused: unscoped candidate"
        return result

    infra_prefixes = ("sandbox/", "egress/", "credentials/", "infra/")
    for path in paths:
        norm = normalize_lab_path(path)
        if any(is_under_prefix(norm, p) or norm.startswith(p.rstrip("/")) for p in infra_prefixes):
            result.infrastructure_touch = True
            result.surfaces.add("infrastructure")
        surface = _surface_for_path(path, manifest)
        if surface:
            result.surfaces.add(surface)
        elif declared_surface:
            result.surfaces.add(declared_surface)
        else:
            result.refusals.append(f"undeclared path has no surface tag: {path}")

    if declared_surface:
        result.surfaces.add(declared_surface)

    if undeclared_cross_surface(paths, manifest, declared_surface=declared_surface):
        result.undeclared_cross_surface = True
        result.refusals.append(
            "undeclared cross-surface candidate; emit one envelope per surface"
        )

    if result.infrastructure_touch and not allow_infrastructure:
        result.refusals.append(
            "infrastructure blast radius locked by default; require change-control ticket"
        )

    # Primary surface = highest blast rank among resolved surfaces.
    ranked = sorted(
        ((SURFACE_BLAST_RANK.get(s, 99), s) for s in result.surfaces),
        reverse=True,
    )
    if ranked:
        result.blast_rank, result.primary_surface = ranked[0]
        result.required_evidence = list(
            MINIMUM_EVIDENCE.get(result.primary_surface, ("held_out_task_metric",))
        )

    missing_evidence = [
        key for key in result.required_evidence if not _evidence_present(evidence, key)
    ]
    if missing_evidence:
        result.refusals.append(
            "missing required evidence: " + ", ".join(missing_evidence)
        )

    if result.refusals:
        result.accepted = False
        result.message = "blast radius refused: " + "; ".join(result.refusals)
        return result

    result.accepted = True
    result.message = (
        f"blast radius accepted: primary={result.primary_surface} "
        f"rank={result.blast_rank}"
    )
    return result
