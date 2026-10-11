"""Refuse candidate envelopes that attempt sandbox profile widening."""

from __future__ import annotations

import re
from typing import Any

from rsi_core.types import LockedPathError

_PROFILE_PATH_RE = re.compile(
    r"(sandbox_profile|profiles?/|isolation/profile)",
    re.I,
)
_WIDENING_HINTS = (
    re.compile(r"widening_allowed\s*[:=]\s*true", re.I),
    re.compile(r"egress_allow", re.I),
    re.compile(r"max_wall_seconds", re.I),
    re.compile(r"credential_ttl", re.I),
    re.compile(r"blocked_paths", re.I),
    re.compile(r"wider\s+egress|open\s+network|raise\s+budget", re.I),
)

_LOCKED_PROFILE_FIELDS = frozenset(
    {
        "widening_allowed",
        "egress_allow",
        "blocked_paths",
        "credential_ttl_seconds",
        "resource_budget",
        "filesystem_jail",
        "allowlist_paths",
    }
)


class WideningViolation(LockedPathError):
    """Raised when a candidate proposes locked profile mutation."""

    def __init__(self, detail: str) -> None:
        super().__init__("sandbox_profile", message=detail)


def assert_no_widening(
    candidate: dict[str, Any],
    *,
    locked_profile: dict[str, Any] | None = None,
) -> None:
    """Fail closed if paths, hypothesis text, or patch touch locked profile fields."""
    paths = [str(p) for p in (candidate.get("paths") or candidate.get("diff_paths") or [])]
    for path in paths:
        if _PROFILE_PATH_RE.search(path):
            raise WideningViolation(f"candidate path touches profile store: {path}")

    hypothesis = str(candidate.get("hypothesis") or candidate.get("summary") or "")
    for pat in _WIDENING_HINTS:
        if pat.search(hypothesis):
            raise WideningViolation(f"hypothesis requests profile widening: {pat.pattern}")

    patch = candidate.get("profile_patch") or candidate.get("sandbox_patch") or {}
    if isinstance(patch, dict):
        touched = _LOCKED_PROFILE_FIELDS & set(patch)
        if touched:
            raise WideningViolation(f"profile_patch touches locked fields: {sorted(touched)}")
        if patch.get("widening_allowed") is True:
            raise WideningViolation("widening_allowed cannot be set true by proposer")

    if locked_profile is not None:
        if locked_profile.get("widening_allowed") is not False:
            raise WideningViolation("locked profile must set widening_allowed false")
