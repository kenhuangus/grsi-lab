"""Load and validate instances against GRSI JSON Schemas."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

_FORMAT_CHECKER = FormatChecker()

def _resolve_schema_dir() -> Path:
    """Prefer packaged schemas; fall back to repo-root schemas for editable installs."""
    here = Path(__file__).resolve().parent
    candidates = (
        here / "schemas",
        here.parent / "schemas",
    )
    for candidate in candidates:
        if (candidate / "ownership_manifest.schema.json").is_file():
            return candidate
    raise FileNotFoundError(
        "GRSI JSON schemas not found. Expected rsi_core/schemas/ or repo schemas/."
    )


SCHEMA_DIR = _resolve_schema_dir()

SCHEMA_NAMES = (
    "ownership_manifest",
    "candidate_diff",
    "compute_request",
    "sandbox_profile",
    "metric_card",
    "sealed_decision",
    "promotion_token",
    "delegation_channel",
)


@cache
def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by short name (without ``.schema.json``)."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"Unknown schema: {name!r}; choose from {SCHEMA_NAMES}")
    path = SCHEMA_DIR / f"{name}.schema.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_instance(name: str, instance: dict[str, Any]) -> dict[str, Any]:
    """Validate ``instance`` against named schema; return instance on success.

    Raises
    ------
    jsonschema.ValidationError
        If the instance does not satisfy the schema.
    """
    schema = load_schema(name)
    validator = Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)
    validator.validate(instance)
    return instance


def is_valid(name: str, instance: dict[str, Any]) -> bool:
    """Return True if ``instance`` validates against the named schema."""
    try:
        validate_instance(name, instance)
        return True
    except ValidationError:
        return False
