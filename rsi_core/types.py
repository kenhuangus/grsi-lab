"""Shared types for GRSI lab contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import NewType
from uuid import UUID, uuid4


class Surface(StrEnum):
    """Stack area a candidate may mutate (CONTRACTS.md surface tags)."""

    MODEL = "model"
    DATA = "data"
    ORCHESTRATION = "orchestration"
    RESEARCH_PROCESS = "research_process"


class LockedPathError(PermissionError):
    """Raised when a write targets a Last Frozen Layer / locked path."""

    def __init__(self, path: str, message: str | None = None) -> None:
        self.path = path
        detail = message or f"Write rejected: path is locked ({path})"
        super().__init__(detail)


LineageId = NewType("LineageId", str)


def new_lineage_id() -> LineageId:
    """Return a new lineage UUID string."""
    return LineageId(str(uuid4()))


def parse_lineage_id(value: str) -> LineageId:
    """Validate and wrap a lineage UUID string."""
    try:
        UUID(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid lineage_id: {value!r}") from exc
    return LineageId(value)
