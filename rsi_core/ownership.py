"""Ownership manifest load and locked-path enforcement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from rsi_core.schemas_load import validate_instance
from rsi_core.types import LockedPathError


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load and schema-validate an ownership manifest (JSON or YAML)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Ownership manifest must be a JSON/YAML object")
    return validate_instance("ownership_manifest", data)


def locked_paths(manifest: dict[str, Any]) -> set[str]:
    """Return the set of locked (Last Frozen Layer) paths."""
    return {str(p) for p in manifest.get("locked", [])}


def _normalize(path: str) -> str:
    return path.replace("\\", "/").rstrip("/")


def is_locked(path: str, manifest: dict[str, Any]) -> bool:
    """True if ``path`` equals or is under a locked prefix."""
    target = _normalize(path)
    for locked in locked_paths(manifest):
        prefix = _normalize(locked)
        if target == prefix or target.startswith(prefix + "/"):
            return True
    return False


def assert_writable(path: str, manifest: dict[str, Any]) -> None:
    """Raise ``LockedPathError`` if ``path`` is under a locked prefix."""
    if is_locked(path, manifest):
        raise LockedPathError(path)


def reject_locked_writes(
    paths: list[str],
    manifest: dict[str, Any],
) -> None:
    """Reject a batch of write paths against the ownership manifest."""
    for path in paths:
        assert_writable(path, manifest)
