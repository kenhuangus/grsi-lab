"""Ownership manifest modularity validation for Chapter 2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rsi_core.ownership import load_manifest
from rsi_core.paths import is_under_prefix, normalize_lab_path
from rsi_core.schemas_load import validate_instance

REQUIRED_COMPONENT_FIELDS = (
    "path",
    "owner",
    "eval_hook",
    "rollback_unit",
    "observability_signal",
)

# Paths that must appear in ``locked`` before overnight RSI is enabled.
DEFAULT_LAST_FROZEN_PREFIXES = (
    "eval/",
    "evaluators/",
    "held_out/",
    "metric_cards/",
    "ledger/",
    "sandbox/",
    "promotion/",
    "safety/",
    "ownership/",
    "schemas/",
    "CONTRACTS.md",
)


def validate_modularity(manifest: dict[str, Any]) -> list[str]:
    """Return modularity contract violations (empty list means structurally eligible).

    Checks schema fields, required modularity columns, and overlap between
    declared mutable ``components`` paths and the Last Frozen Layer ``locked`` list.
    """
    validate_instance("ownership_manifest", manifest)
    errors: list[str] = []
    components = manifest.get("components") or []
    locked = [normalize_lab_path(str(p)) for p in manifest.get("locked") or []]

    for i, comp in enumerate(components):
        for field in REQUIRED_COMPONENT_FIELDS:
            value = comp.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"components[{i}].{field} missing or empty")
        path = normalize_lab_path(str(comp.get("path", "")))
        if not path:
            continue
        for locked_path in locked:
            if is_under_prefix(path, locked_path) or is_under_prefix(locked_path, path):
                errors.append(
                    f"components[{i}].path {path!r} overlaps locked path {locked_path!r}"
                )

    if not locked:
        errors.append("locked list is empty; Last Frozen Layer is not declared")

    return errors


def validate_manifest_file(path: str | Path) -> list[str]:
    """Load a manifest file (JSON/YAML) and return modularity violations."""
    manifest = load_manifest(path)
    return validate_modularity(manifest)


def component_paths(manifest: dict[str, Any]) -> set[str]:
    """Return normalized mutable component paths from the manifest."""
    return {
        normalize_lab_path(str(c["path"]))
        for c in manifest.get("components") or []
        if c.get("path")
    }


def path_is_declared(path: str, manifest: dict[str, Any]) -> bool:
    """True if ``path`` equals or sits under a declared mutable component path."""
    target = normalize_lab_path(path)
    for declared in component_paths(manifest):
        if is_under_prefix(target, declared) or target == declared:
            return True
        # Component path may be a file; allow exact file match only.
        if declared == target:
            return True
    return False


def missing_last_frozen_prefixes(manifest: dict[str, Any]) -> list[str]:
    """Return canonical Last Frozen Layer prefixes absent from ``locked``."""
    locked = [normalize_lab_path(str(p)) for p in manifest.get("locked") or []]
    missing: list[str] = []
    for prefix in DEFAULT_LAST_FROZEN_PREFIXES:
        norm = normalize_lab_path(prefix)
        covered = any(
            is_under_prefix(norm, locked_path) or is_under_prefix(locked_path, norm)
            or locked_path == norm
            for locked_path in locked
        )
        if not covered:
            missing.append(prefix)
    return missing
