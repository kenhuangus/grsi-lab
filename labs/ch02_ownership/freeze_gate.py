"""Last Frozen Layer freeze gate — must pass before automated RSI is enabled."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from labs.ch02_ownership.manifest import (
    DEFAULT_LAST_FROZEN_PREFIXES,
    missing_last_frozen_prefixes,
    validate_modularity,
)
from rsi_core.ownership import is_locked
from rsi_core.paths import normalize_lab_path


class FreezeStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    BREAK_OPEN = "break_open"


# Canonical checklist items from Chapter 2 operational freeze gate.
FREEZE_CHECKLIST_ITEMS = (
    "metric_card_registered",
    "external_evaluator_pinned",
    "sealed_ledger_append_only",
    "sandbox_profile_frozen",
    "promotion_keys_human_held",
    "safety_constitution_locked",
    "ownership_manifest_locked",
)

# These two are verified via locked-path membership, not file artifacts.
_LOCK_VERIFIED_ITEMS = frozenset(
    {"ownership_manifest_locked", "safety_constitution_locked"}
)

# True claims for these items require evidence_paths artifacts (not bare booleans).
ARTIFACT_CHECKLIST_ITEMS = tuple(
    item for item in FREEZE_CHECKLIST_ITEMS if item not in _LOCK_VERIFIED_ITEMS
)


@dataclass
class FreezeGateResult:
    """Outcome of the Last Frozen Layer freeze gate."""

    status: FreezeStatus
    checklist: dict[str, bool] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    break_ticket: str | None = None
    message: str = ""

    @property
    def passed(self) -> bool:
        return self.status is FreezeStatus.PASSED


def _checklist_from_evidence(evidence: dict[str, bool] | None) -> dict[str, bool]:
    evidence = evidence or {}
    return {item: bool(evidence.get(item, False)) for item in FREEZE_CHECKLIST_ITEMS}


def _normalize_path_spec(spec: str | Mapping[str, Any]) -> tuple[str, str | None]:
    """Return (path, optional expected sha256 hex) from an evidence path spec."""
    if isinstance(spec, str):
        return spec, None
    path = str(spec.get("path") or "")
    expected = spec.get("sha256") or spec.get("hash")
    return path, (str(expected) if expected else None)


def _verify_evidence_artifact(item: str, spec: str | Mapping[str, Any]) -> str | None:
    """Return a failure message if the artifact is missing or hash-mismatched."""
    path_str, expected_sha = _normalize_path_spec(spec)
    if not path_str.strip():
        return f"evidence path empty for checklist item: {item}"
    path = Path(path_str)
    if not path.is_file():
        return f"evidence artifact missing for {item}: {path_str}"
    if expected_sha is not None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest.lower() != expected_sha.lower():
            return (
                f"evidence hash mismatch for {item}: "
                f"expected {expected_sha}, got {digest}"
            )
    return None


def run_freeze_gate(
    manifest: dict[str, Any],
    *,
    evidence: dict[str, bool] | None = None,
    evidence_paths: Mapping[str, str | Mapping[str, Any]] | None = None,
    manifest_path: str = "ownership/manifest.json",
    safety_path: str = "safety/constitution.md",
    break_ticket: str | None = None,
    break_paths: list[str] | None = None,
) -> FreezeGateResult:
    """Evaluate whether automated RSI may be enabled against this manifest.

    Fail-closed rules:
    - Modularity validation must produce zero errors.
    - *Every* canonical Last Frozen Layer prefix must be covered by ``locked``.
    - Operational checklist evidence must be true for every item.
    - Artifact checklist True claims *always* require ``evidence_paths`` entries
      pointing at real files (optional sha256). Bare booleans alone never pass.
    - ``manifest_path`` and ``safety_path`` must be locked.
    - An open freeze-break ticket yields ``break_open`` — RSI still disabled.
    """
    failures: list[str] = []
    checklist = _checklist_from_evidence(evidence)
    paths = dict(evidence_paths or {})

    modularity_errors = validate_modularity(manifest)
    failures.extend(f"modularity: {e}" for e in modularity_errors)

    missing = missing_last_frozen_prefixes(manifest)
    if missing:
        failures.append(
            "locked coverage incomplete: missing "
            + ", ".join(missing)
            + f" ({len(missing)}/{len(DEFAULT_LAST_FROZEN_PREFIXES)} canonical prefixes)"
        )

    for item in ARTIFACT_CHECKLIST_ITEMS:
        ok = checklist.get(item, False)
        if not ok:
            continue
        spec = paths.get(item)
        if spec is None:
            checklist[item] = False
            failures.append(
                f"checklist unmet: {item} (boolean True without evidence path)"
            )
            continue
        err = _verify_evidence_artifact(item, spec)
        if err is not None:
            checklist[item] = False
            failures.append(err)

    for item, spec in paths.items():
        if item not in ARTIFACT_CHECKLIST_ITEMS:
            continue
        err = _verify_evidence_artifact(item, spec)
        if err is not None and err not in failures:
            checklist[item] = False
            failures.append(err)

    for item, ok in checklist.items():
        if not ok:
            msg = f"checklist unmet: {item}"
            if msg not in failures and not any(
                f.startswith(f"checklist unmet: {item}")
                or f.startswith(f"evidence artifact missing for {item}")
                or f.startswith(f"evidence hash mismatch for {item}")
                or f.startswith(f"evidence path empty for checklist item: {item}")
                for f in failures
            ):
                failures.append(msg)

    if not is_locked(manifest_path, manifest):
        failures.append(f"ownership manifest path not locked: {manifest_path}")
        checklist["ownership_manifest_locked"] = False
    else:
        checklist["ownership_manifest_locked"] = True

    if not is_locked(safety_path, manifest):
        failures.append(f"safety constitution path not locked: {safety_path}")
        checklist["safety_constitution_locked"] = False
    else:
        checklist["safety_constitution_locked"] = True

    if break_ticket:
        recorded = [normalize_lab_path(p) for p in (break_paths or [])]
        if not recorded:
            failures.append(
                f"freeze-break ticket {break_ticket!r} lacks break_paths; RSI disabled"
            )
        return FreezeGateResult(
            status=FreezeStatus.BREAK_OPEN,
            checklist=checklist,
            failures=failures
            + [f"freeze-break open: ticket={break_ticket} paths={recorded}"],
            break_ticket=break_ticket,
            message="freeze gate open under break ticket; automated RSI disabled",
        )

    if failures:
        return FreezeGateResult(
            status=FreezeStatus.FAILED,
            checklist=checklist,
            failures=failures,
            message="freeze gate failed; automated RSI disabled",
        )

    return FreezeGateResult(
        status=FreezeStatus.PASSED,
        checklist=checklist,
        failures=[],
        message="freeze gate passed; automated RSI may be enabled",
    )
