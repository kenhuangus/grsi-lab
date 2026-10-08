"""Sandbox profile enforcement with a real filesystem jail root."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
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
    "fixtures/datasets/",
    "fixtures/metric_cards/",
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
    for blocked in profile.get("blocked_paths", []):
        if is_under_prefix(path, str(blocked)):
            return True
    return False


def path_in_allowlist(path: str, profile: dict[str, Any]) -> bool:
    allow = profile.get("allowlist_paths") or []
    if not allow:
        return False  # deny-by-default when empty
    return any(is_under_prefix(path, str(entry)) for entry in allow)


def create_filesystem_jail(base: str | Path | None = None) -> Path:
    """Create a real temporary jail directory with work/ subtree."""
    root = Path(base) if base else Path(tempfile.mkdtemp(prefix="grsi-jail-"))
    (root / "work").mkdir(parents=True, exist_ok=True)
    return root.resolve()


def resolve_in_jail(jail: Path, path: str) -> Path:
    """Resolve path inside jail; raise if escape attempted."""
    jail = jail.resolve()
    # Absolute lab logical paths like /sandbox/work/... map under jail root
    norm = normalize_lab_path(path)
    if norm.startswith("/"):
        # strip logical jail prefix if present
        parts = norm.lstrip("/").split("/", 1)
        if len(parts) > 1 and parts[0] in {"sandbox", jail.name}:
            rel = parts[1]
        else:
            rel = norm.lstrip("/")
    else:
        rel = norm
    target = (jail / rel).resolve()
    if not str(target).startswith(str(jail)):
        raise SandboxViolation(path, reason=f"Sandbox jail escape: {path}")
    return target


def assert_sandbox_allows(
    paths: list[str],
    profile: dict[str, Any],
    *,
    jail_root: str | Path | None = None,
) -> None:
    """Raise ``SandboxViolation`` if any path is blocked or outside policy.

    When ``jail_root`` is provided, also resolves each path against the real FS jail.
    """
    validated = load_profile(profile)
    if validated.get("widening_allowed") is not False:
        raise SandboxViolation("*", reason="widening_allowed must be false")

    # Resource budget must be present and positive (enforced as contract, not OS cgroup)
    budget = validated["resource_budget"]
    if float(budget["cpu_cores"]) <= 0 or int(budget["memory_mb"]) < 1:
        raise SandboxViolation("*", reason="invalid resource_budget")
    if int(budget["max_wall_seconds"]) < 1:
        raise SandboxViolation("*", reason="invalid max_wall_seconds")
    if int(validated["credential_ttl_seconds"]) < 1:
        raise SandboxViolation("*", reason="invalid credential_ttl_seconds")

    jail_logical = str(validated["filesystem_jail"])
    for path in paths:
        norm = normalize_lab_path(path)
        if path_blocked(norm, validated):
            raise SandboxViolation(path)
        if norm.startswith(".."):
            raise SandboxViolation(path, reason=f"Sandbox rejects parent traversal: {path}")

        if norm.startswith("/"):
            if not is_inside_jail(norm, jail_logical):
                raise SandboxViolation(
                    path, reason=f"Sandbox jail escape: {path} outside {jail_logical}"
                )
            if not path_in_allowlist(norm, validated):
                raise SandboxViolation(path, reason=f"Sandbox allowlist miss: {path}")
        else:
            # Relative paths must map under allowlist when interpreted as jail-relative
            jail_rel = normalize_lab_path(f"{jail_logical.rstrip('/')}/work/{norm}")
            if not path_in_allowlist(jail_rel, validated) and not path_in_allowlist(
                normalize_lab_path(f"{jail_logical.rstrip('/')}/{norm}"), validated
            ):
                # Allow short relative work paths that normalize under /jail/work
                if not is_under_prefix(jail_rel, f"{jail_logical.rstrip('/')}/work"):
                    raise SandboxViolation(path, reason=f"Sandbox allowlist miss: {path}")

        if jail_root is not None:
            resolve_in_jail(Path(jail_root), path)


def materialize_candidate_paths(
    paths: list[str],
    *,
    jail_root: Path,
    content: bytes = b"candidate\n",
) -> list[Path]:
    """Write candidate files inside the real jail (proves FS binding)."""
    written: list[Path] = []
    for path in paths:
        target = resolve_in_jail(jail_root, path if path.startswith("/") else f"work/{path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        # Ensure not world-writable when possible
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
        written.append(target)
    return written


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
