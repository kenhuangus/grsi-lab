"""Shim — canonical implementation lives in ``labs.ch07_isolation.sandbox_profile``."""

from labs.ch07_isolation.sandbox_profile import (  # noqa: F401
    DEFAULT_EVALUATOR_PATHS,
    SandboxViolation,
    assert_sandbox_allows,
    create_filesystem_jail,
    default_lab_profile,
    load_profile,
    materialize_candidate_paths,
    path_blocked,
    path_in_allowlist,
    resolve_in_jail,
)

__all__ = [
    "DEFAULT_EVALUATOR_PATHS",
    "SandboxViolation",
    "assert_sandbox_allows",
    "create_filesystem_jail",
    "default_lab_profile",
    "load_profile",
    "materialize_candidate_paths",
    "path_blocked",
    "path_in_allowlist",
    "resolve_in_jail",
]
