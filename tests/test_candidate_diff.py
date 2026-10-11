"""Tests for candidate_diff schema rejection."""

from __future__ import annotations

import pytest
from jsonschema import ValidationError

from labs.ch03_proposals.reject_gates import build_proposal
from rsi_core.schemas_load import validate_instance
from rsi_core.types import LockedPathError, Surface


def test_invalid_candidate_diff_rejected() -> None:
    bad = {
        "lineage_id": "not-a-uuid",
        "surface": "model",
        "hypothesis": "x",
        "metric": "y",
        "rollback": {"unit": "u", "snapshot_ref": "s"},
        "diff": {"paths": ["a"], "summary": "s"},
        "proposer_role": "planner",
    }
    with pytest.raises(ValidationError):
        validate_instance("candidate_diff", bad)


def test_missing_required_field_rejected() -> None:
    incomplete = {
        "lineage_id": "12345678-1234-4234-8234-123456789abc",
        "surface": "model",
        "hypothesis": "h",
        # metric missing
        "rollback": {"unit": "u", "snapshot_ref": "s"},
        "diff": {"paths": ["a"], "summary": "s"},
        "proposer_role": "implementer",
    }
    with pytest.raises(ValidationError):
        validate_instance("candidate_diff", incomplete)


def test_valid_candidate_via_engine() -> None:
    manifest = {
        "version": "1.0",
        "components": [
            {
                "path": "data/buffer/",
                "owner": "lab",
                "eval_hook": "e",
                "rollback_unit": "data.buffer",
                "observability_signal": "o",
                "surface": "data",
            }
        ],
        "locked": ["eval/", "held_out/", "metric_cards/", "ledger/", "ownership/"],
    }
    env = build_proposal(
        surface=Surface.DATA,
        hypothesis="Admit filtered experience only",
        metric="admission_precision",
        paths=["data/buffer/"],
        summary="admission gate",
        rollback_unit="data.buffer",
        snapshot_ref="snap://buffer@0",
        proposer_role="planner",
        ownership_manifest=manifest,
        require_manifest=True,
    )
    assert env["surface"] == "data"


def test_proposal_rejects_locked_paths() -> None:
    manifest = {
        "version": "1.0",
        "components": [
            {
                "path": "harness/x.py",
                "owner": "lab",
                "eval_hook": "e",
                "rollback_unit": "r",
                "observability_signal": "o",
            }
        ],
        "locked": ["eval/"],
    }
    with pytest.raises(LockedPathError):
        build_proposal(
            surface=Surface.MODEL,
            hypothesis="touch eval",
            metric="m",
            paths=["eval/scorer.py"],
            summary="bad",
            rollback_unit="r",
            snapshot_ref="s",
            proposer_role="implementer",
            ownership_manifest=manifest,
        )
