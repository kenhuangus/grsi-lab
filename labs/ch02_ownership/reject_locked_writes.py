"""Fail-closed locked-path and undeclared-path rejection for Chapter 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from labs.ch02_ownership.manifest import path_is_declared
from rsi_core.ownership import assert_writable, is_locked
from rsi_core.ownership import reject_locked_writes as _core_reject
from rsi_core.paths import normalize_lab_path
from rsi_core.types import LockedPathError

RejectClass = Literal["locked_path", "undeclared_path", "parent_traversal"]


@dataclass(frozen=True)
class PathReject:
    """One refused write path with a stable reject class."""

    path: str
    reject_class: RejectClass
    message: str


@dataclass
class RejectReport:
    """Batch reject outcome for a candidate path list."""

    accepted: bool
    rejects: list[PathReject] = field(default_factory=list)

    @property
    def messages(self) -> list[str]:
        return [r.message for r in self.rejects]


def classify_write_path(path: str, manifest: dict[str, Any]) -> PathReject | None:
    """Return a PathReject if the write must be refused, else None."""
    norm = normalize_lab_path(path)
    if norm.startswith("..") or norm == "..":
        return PathReject(
            path=path,
            reject_class="parent_traversal",
            message=f"Write rejected: parent traversal not allowed ({path})",
        )
    if is_locked(path, manifest):
        return PathReject(
            path=path,
            reject_class="locked_path",
            message=f"Write rejected: path is locked ({path})",
        )
    if not path_is_declared(path, manifest):
        return PathReject(
            path=path,
            reject_class="undeclared_path",
            message=f"Write rejected: path is undeclared in components ({path})",
        )
    return None


def assert_paths_writable(
    paths: list[str],
    manifest: dict[str, Any],
    *,
    require_declared: bool = True,
) -> None:
    """Raise LockedPathError on the first refused path (fail closed).

    When ``require_declared`` is True (default for Chapter 2 labs), paths that are
    neither locked nor listed under ``components`` are refused as undeclared.
    """
    for path in paths:
        if require_declared:
            refuse = classify_write_path(path, manifest)
            if refuse is not None:
                raise LockedPathError(path, message=refuse.message)
        else:
            assert_writable(path, manifest)


def reject_locked_writes(
    paths: list[str],
    manifest: dict[str, Any],
    *,
    require_declared: bool = False,
) -> None:
    """Reject locked (and optionally undeclared) write paths.

    Default ``require_declared=False`` preserves the Chapter 3 proposal-engine
    contract that only LockedPathError fires on Last Frozen Layer hits. Chapter 2
    CLI and freeze drills pass ``require_declared=True``.
    """
    if require_declared:
        assert_paths_writable(paths, manifest, require_declared=True)
    else:
        _core_reject(paths, manifest)


def inspect_writes(
    paths: list[str],
    manifest: dict[str, Any],
    *,
    require_declared: bool = True,
) -> RejectReport:
    """Inspect all paths and return a report without raising (for CLI/telemetry)."""
    rejects: list[PathReject] = []
    for path in paths:
        if require_declared:
            refuse = classify_write_path(path, manifest)
            if refuse is not None:
                rejects.append(refuse)
        else:
            try:
                assert_writable(path, manifest)
            except LockedPathError as exc:
                rejects.append(
                    PathReject(
                        path=path,
                        reject_class="locked_path",
                        message=str(exc),
                    )
                )
    return RejectReport(accepted=not rejects, rejects=rejects)
