"""Sandbox profile enforcement — jail, allowlist, and blocked evaluator paths."""

from __future__ import annotations

from typing import Any

from rsi_core.paths import is_inside_jail, is_under_prefix, normalize_lab_path
from rsi_core.schemas_load import validate_instance
from rsi_core.types import LockedPathError

DEFAULT_EVALUATOR_PATHS = (
    "eval/",
    "evaluators/",
    "held_out/",
    "metric_cards/",
    "ledger/",
)


class SandboxViolation(LockedPathError):
    """Raised when a candidate touches a blocked or out-of-jail path."""

    def __init__(self, path: str, *, reason: str | None = None) -> None:
        message = reason or f"Sandbox blocks evaluator/frozen path: {path}"
        super().__init__(path, message=message)


def load_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a sandbox_profile instance."""
    if "widening_allowed" not in profile:
        profile = {**profile, "widening_allowed": False}
    return validate_instance("sandbox_profile", profile)


def path_blocked(path: str, profile: dict[str, Any]) -> bool:
    """True if ``path`` equals or is under a blocked prefix in the profile."""
    for blocked in profile.get("blocked_paths", []):
        if is_under_prefix(path, str(blocked)):
            return True
    return False


def path_in_allowlist(path: str, profile: dict[str, Any]) -> bool:
    """True if path is under an allowlist entry (when allowlist is non-empty)."""
    allow = profile.get("allowlist_paths") or []
    if not allow:
        return True
    return any(is_under_prefix(path, str(entry)) for entry in allow)


def assert_sandbox_allows(paths: list[str], profile: dict[str, Any]) -> None:
    """Raise ``SandboxViolation`` if any path is blocked or outside policy.

    Relative short paths (``adapters/...``) are allowed when not blocked — that
    matches Packt lab ergonomics. Absolute paths must stay inside
    ``filesystem_jail`` and, when configured, the allowlist. Parent traversal
    that normalizes onto a blocked prefix is rejected via ``path_blocked``.
    """
    validated = load_profile(profile)
    jail = str(validated["filesystem_jail"])
    for path in paths:
        norm = normalize_lab_path(path)
        if path_blocked(norm, validated):
            raise SandboxViolation(path)
        if norm.startswith(".."):
            raise SandboxViolation(
                path,
                reason=f"Sandbox rejects parent traversal: {path}",
            )
        if norm.startswith("/"):
            if not is_inside_jail(norm, jail):
                raise SandboxViolation(
                    path,
                    reason=f"Sandbox jail escape: {path} outside {jail}",
                )
            if not path_in_allowlist(norm, validated):
                raise SandboxViolation(
                    path,
                    reason=f"Sandbox allowlist miss: {path}",
                )


def default_lab_profile(
    *,
    profile_id: str = "lab-default",
    jail: str = "/sandbox",
) -> dict[str, Any]:
    """Return a schema-valid default sandbox profile for labs."""
    return load_profile(
        {
            "profile_id": profile_id,
            "filesystem_jail": jail,
            "allowlist_paths": [f"{jail}/work"],
            "blocked_paths": list(DEFAULT_EVALUATOR_PATHS),
            "egress_allow": [],
            "credential_ttl_seconds": 600,
            "resource_budget": {
                "cpu_cores": 1,
                "memory_mb": 512,
                "max_wall_seconds": 300,
            },
            "widening_allowed": False,
        }
    )
