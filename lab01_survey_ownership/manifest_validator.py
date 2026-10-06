"""Validate ownership manifests for modularity contract completeness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rsi_core.ownership import load_manifest
from rsi_core.schemas_load import validate_instance


REQUIRED_COMPONENT_FIELDS = (
    "path",
    "owner",
    "eval_hook",
    "rollback_unit",
    "observability_signal",
)


def validate_modularity(manifest: dict[str, Any]) -> list[str]:
    """Return a list of modularity contract violations (empty if ok)."""
    validate_instance("ownership_manifest", manifest)
    errors: list[str] = []
    for i, comp in enumerate(manifest.get("components", [])):
        for field in REQUIRED_COMPONENT_FIELDS:
            if not comp.get(field):
                errors.append(f"components[{i}].{field} missing or empty")
        # Locked paths must not also be listed as mutable RSI targets
        path = str(comp.get("path", ""))
        for locked in manifest.get("locked", []):
            if path == locked or path.startswith(str(locked).rstrip("/") + "/"):
                errors.append(
                    f"components[{i}].path {path!r} overlaps locked path {locked!r}"
                )
    return errors


def validate_manifest_file(path: str | Path) -> list[str]:
    """Load a manifest file and return modularity violations."""
    manifest = load_manifest(path)
    return validate_modularity(manifest)
