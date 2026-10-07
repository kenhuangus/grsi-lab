"""Tests for sandbox blocking of evaluator paths."""

from __future__ import annotations

import pytest

from lab04_isolation_eval.sandbox import (
    SandboxViolation,
    assert_sandbox_allows,
    default_lab_profile,
    path_blocked,
)


def test_sandbox_blocks_evaluator_path() -> None:
    profile = default_lab_profile()
    assert path_blocked("eval/scorer.py", profile)
    with pytest.raises(SandboxViolation):
        assert_sandbox_allows(["eval/scorer.py"], profile)


def test_sandbox_allows_work_path() -> None:
    profile = default_lab_profile()
    assert not path_blocked("adapters/candidate/", profile)
    assert_sandbox_allows(["adapters/candidate/"], profile)


def test_held_out_blocked() -> None:
    profile = default_lab_profile()
    with pytest.raises(SandboxViolation):
        assert_sandbox_allows(["held_out/private.jsonl"], profile)


def test_parent_traversal_onto_blocked_prefix() -> None:
    profile = default_lab_profile()
    with pytest.raises(SandboxViolation):
        assert_sandbox_allows(["work/../../eval/scorer.py"], profile)


def test_absolute_jail_escape_blocked() -> None:
    profile = default_lab_profile()
    with pytest.raises(SandboxViolation, match="jail escape"):
        assert_sandbox_allows(["/etc/passwd"], profile)


def test_absolute_allowlist_required() -> None:
    profile = default_lab_profile()
    with pytest.raises(SandboxViolation, match="allowlist"):
        assert_sandbox_allows(["/sandbox/other/file.py"], profile)


def test_absolute_allowlisted_work_path() -> None:
    profile = default_lab_profile()
    assert_sandbox_allows(["/sandbox/work/candidate.py"], profile)
