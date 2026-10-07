"""Failure atlas — index governance failures by RSI loop step."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOOP_STEPS = (
    "propose",
    "isolate",
    "verify_measure",
    "keep_revert",
    "archive",
    "promote",
    "audit",
)

DEFAULT_SEED = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "failure_atlas"
    / "seed_entries.json"
)


def load_entries(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load failure atlas entries from JSON."""
    path = Path(path) if path else DEFAULT_SEED
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("failure atlas seed must be a JSON array")
    return data


def by_loop_step(
    entries: list[dict[str, Any]],
    step: str,
) -> list[dict[str, Any]]:
    """Filter entries keyed by RSI loop step."""
    if step not in LOOP_STEPS:
        raise ValueError(f"Unknown loop step {step!r}; choose from {LOOP_STEPS}")
    return [e for e in entries if e.get("loop_step") == step]


def index_by_step(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group entries by ``loop_step``."""
    index: dict[str, list[dict[str, Any]]] = {s: [] for s in LOOP_STEPS}
    for entry in entries:
        step = entry.get("loop_step")
        if step in index:
            index[step].append(entry)
    return index
