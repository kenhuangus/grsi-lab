"""Lab path normalization — defeat ``..`` and separator tricks."""

from __future__ import annotations

import posixpath


def normalize_lab_path(path: str) -> str:
    """Normalize a lab-relative path for prefix and jail checks.

    Uses POSIX rules (labs treat paths as logical prefixes, not OS paths).
    Collapses ``.`` / ``..``, unifies separators, strips a trailing slash
    (except the root ``/``).
    """
    raw = str(path).replace("\\", "/")
    if not raw:
        return ""
    absolute = raw.startswith("/")
    normalized = posixpath.normpath(raw)
    # posixpath.normpath("") -> "."; keep empty distinct
    if raw in {"", "."} and normalized == ".":
        return ""
    if absolute and not normalized.startswith("/"):
        normalized = "/" + normalized
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


def is_under_prefix(path: str, prefix: str) -> bool:
    """True if ``path`` equals or is nested under ``prefix`` after normalize."""
    target = normalize_lab_path(path)
    base = normalize_lab_path(prefix)
    if not base:
        return False
    if target == base:
        return True
    # Ensure directory boundary (eval vs evaluation)
    return target.startswith(base.rstrip("/") + "/")


def is_inside_jail(path: str, jail: str) -> bool:
    """True if ``path`` is inside the filesystem jail after normalize."""
    return is_under_prefix(path, jail)
