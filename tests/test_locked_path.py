"""Tests for locked-path rejection via ownership manifest."""

from __future__ import annotations

import pytest

from rsi_core.ownership import assert_writable, reject_locked_writes
from rsi_core.types import LockedPathError


MANIFEST = {
    "version": "1.0",
    "components": [
        {
            "path": "harness/foo.py",
            "owner": "lab",
            "eval_hook": "eval/score",
            "rollback_unit": "harness.foo",
            "observability_signal": "foo_ok",
        }
    ],
    "locked": ["eval/", "held_out/", "ledger/", "CONTRACTS.md"],
}


def test_locked_path_rejection() -> None:
    with pytest.raises(LockedPathError) as exc:
        assert_writable("eval/scorer.py", MANIFEST)
    assert exc.value.path == "eval/scorer.py"


def test_locked_exact_file() -> None:
    with pytest.raises(LockedPathError):
        assert_writable("CONTRACTS.md", MANIFEST)


def test_mutable_path_allowed() -> None:
    assert_writable("harness/foo.py", MANIFEST)
    reject_locked_writes(["adapters/v1/", "harness/foo.py"], MANIFEST)


def test_batch_rejects_on_first_locked() -> None:
    with pytest.raises(LockedPathError):
        reject_locked_writes(["harness/ok.py", "held_out/set.json"], MANIFEST)
