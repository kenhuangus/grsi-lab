"""Sandbox profile enforcement — blocked evaluator paths."""

from __future__ import annotations

from typing import Any

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
    """Raised when a candidate touches a blocked sandbox path."""

    def __init__(self, path: str) -> None:
        super().__init__(path, message=f"Sandbox blocks evaluator/frozen path: {path}")


def load_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a sandbox_profile instance."""
    if "widening_allowed" not in profile:
        profile = {**profile, "widening_allowed": False}
    return validate_instance("sandbox_profile", profile)


def _normalize(path: str) -> str:
    return path.replace("\\", "/").rstrip("/")


def path_blocked(path: str, profile: dict[str, Any]) -> bool:
    """True if ``path`` equals or is under a blocked prefix in the profile."""
    target = _normalize(path)
    for blocked in profile.get("blocked_paths", []):
        prefix = _normalize(str(blocked))
        if not prefix:
            continue
        if target == prefix or target.startswith(prefix + "/"):
            return True
    return False


def assert_sandbox_allows(paths: list[str], profile: dict[str, Any]) -> None:
    """Raise ``SandboxViolation`` if any path is blocked."""
    validated = load_profile(profile)
    for path in paths:
        if path_blocked(path, validated):
            raise SandboxViolation(path)


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
