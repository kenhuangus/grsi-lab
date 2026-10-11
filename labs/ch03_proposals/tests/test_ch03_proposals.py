"""Accept + refuse paths for Chapter 3 proposals lab."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from labs.ch03_proposals.compute_request import (
    ComputeBudgetError,
    ComputeBudgetLedger,
    authorize_compute,
    build_compute_request,
)
from labs.ch03_proposals.implementer import implement_proposal
from labs.ch03_proposals.lineage import (
    LineageStatus,
    assert_shared_lineage,
    close_proposal_lineage,
    lineage_is_open,
    reset_registry,
)
from labs.ch03_proposals.planner import plan_then_implement
from labs.ch03_proposals.reject_gates import ProposalRejectError, build_proposal
from rsi_core.types import LockedPathError, Surface

MANIFEST = {
    "version": "1.0",
    "components": [
        {
            "path": "adapters/",
            "owner": "ml",
            "eval_hook": "eval/hooks/adapter.py",
            "rollback_unit": "adapters.v1",
            "observability_signal": "held_out_accuracy",
            "surface": "model",
        }
    ],
    "locked": ["eval/", "held_out/", "metric_cards/", "ledger/", "ownership/"],
}


@pytest.fixture(autouse=True)
def _clean_lineage() -> None:
    reset_registry()


def test_accept_plan_then_implement_shared_lineage() -> None:
    planner, implementer = plan_then_implement(
        "Adapter rank-8 improves held-out accuracy",
        "write adapter_config + weights under adapters/v1/",
        metric="held_out_accuracy",
        paths=["adapters/v1/"],
        rollback_unit="adapters.v1",
        snapshot_ref="snap://adapters/v1@0",
        ownership_manifest=MANIFEST,
        require_manifest=True,
    )
    assert assert_shared_lineage(planner, implementer)
    assert planner["proposer_role"] == "planner"
    assert implementer["proposer_role"] == "implementer"
    assert implementer["diff"]["summary"].startswith("write adapter")
    assert lineage_is_open(planner["lineage_id"])


def test_refuse_locked_path() -> None:
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
            ownership_manifest=MANIFEST,
            require_manifest=True,
        )


def test_refuse_undeclared_path() -> None:
    with pytest.raises(LockedPathError) as exc:
        build_proposal(
            surface=Surface.MODEL,
            hypothesis="touch memory",
            metric="m",
            paths=["memory/rules/admit.yaml"],
            summary="bad",
            rollback_unit="r",
            snapshot_ref="s",
            proposer_role="implementer",
            ownership_manifest=MANIFEST,
            require_manifest=True,
        )
    assert "undeclared" in str(exc.value).lower()


def test_refuse_untestable_empty_metric() -> None:
    with pytest.raises(ProposalRejectError) as exc:
        build_proposal(
            surface=Surface.MODEL,
            hypothesis="gain",
            metric="   ",
            paths=["adapters/v1/"],
            summary="patch",
            rollback_unit="r",
            snapshot_ref="s",
            proposer_role="planner",
            ownership_manifest=MANIFEST,
            require_manifest=True,
        )
    assert exc.value.reject_class == "untestable"


def test_refuse_unscoped_empty_paths() -> None:
    with pytest.raises(ProposalRejectError) as exc:
        build_proposal(
            surface=Surface.MODEL,
            hypothesis="gain",
            metric="held_out_accuracy",
            paths=[],
            summary="patch",
            rollback_unit="r",
            snapshot_ref="s",
            proposer_role="planner",
            ownership_manifest=MANIFEST,
            require_manifest=True,
        )
    assert exc.value.reject_class == "unscoped"


def test_refuse_implementer_scope_expansion() -> None:
    with pytest.raises(ProposalRejectError) as exc:
        implement_proposal(
            surface=Surface.MODEL,
            hypothesis="gain",
            metric="held_out_accuracy",
            paths=["adapters/v1/", "adapters/v2/"],
            summary="expand",
            rollback_unit="r",
            snapshot_ref="s",
            ownership_manifest=MANIFEST,
            approved_paths=["adapters/v1/"],
            require_manifest=True,
        )
    assert exc.value.reject_class == "unscoped"


def test_refuse_compute_cumulative_over_budget() -> None:
    lineage = "12345678-1234-4234-8234-123456789abc"
    ledger = ComputeBudgetLedger()
    request = build_compute_request(
        lineage_id=lineage,
        units="tokens",
        amount=100,
        target_metric="held_out_accuracy",
        stop_rule="wall",
    )
    authorize_compute(request, amount=50, ledger=ledger)
    with pytest.raises(ComputeBudgetError) as exc:
        authorize_compute(request, amount=60, ledger=ledger)
    assert "cumulative" in str(exc.value).lower() or "budget" in str(exc.value).lower()


def test_refuse_authorize_without_shared_ledger() -> None:
    lineage = "12345678-1234-4234-8234-123456789abc"
    request = build_compute_request(
        lineage_id=lineage,
        units="tokens",
        amount=100,
        target_metric="held_out_accuracy",
        stop_rule="wall",
    )
    with pytest.raises(TypeError):
        authorize_compute(request, amount=10)  # type: ignore[call-arg]


def test_close_lineage_keep_revert_reject() -> None:
    planner, _implementer = plan_then_implement(
        "Adapter rank-8 improves held-out accuracy",
        "write adapter_config + weights under adapters/v1/",
        metric="held_out_accuracy",
        paths=["adapters/v1/"],
        rollback_unit="adapters.v1",
        snapshot_ref="snap://adapters/v1@0",
        ownership_manifest=MANIFEST,
    )
    lid = planner["lineage_id"]
    kept = close_proposal_lineage(lid, "keep", reason="metric improved")
    assert kept.status is LineageStatus.KEEP
    assert lineage_is_open(lid) is False

    reset_registry()
    planner2, _ = plan_then_implement(
        "retry",
        "patch",
        metric="held_out_accuracy",
        paths=["adapters/v1/"],
        rollback_unit="adapters.v1",
        snapshot_ref="snap://adapters/v1@1",
        ownership_manifest=MANIFEST,
    )
    lid2 = planner2["lineage_id"]
    reverted = close_proposal_lineage(lid2, "revert", reason="no gain")
    assert reverted.status is LineageStatus.REVERT

    reset_registry()
    planner3, _ = plan_then_implement(
        "bad",
        "patch",
        metric="held_out_accuracy",
        paths=["adapters/v1/"],
        rollback_unit="adapters.v1",
        snapshot_ref="snap://adapters/v1@2",
        ownership_manifest=MANIFEST,
    )
    lid3 = planner3["lineage_id"]
    rejected = close_proposal_lineage(lid3, "reject", reason="unscoped after review")
    assert rejected.status is LineageStatus.REJECT


def test_cli_refuse_locked(tmp_path: Path) -> None:
    from labs.ch03_proposals.cli import main

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    code = main(
        [
            "propose",
            "--manifest",
            str(manifest_path),
            "--hypothesis",
            "touch eval",
            "--metric",
            "m",
            "--paths",
            "eval/scorer.py",
            "--rollback-unit",
            "r",
            "--snapshot-ref",
            "s",
            "--summary",
            "bad",
            "--role",
            "implementer",
        ]
    )
    assert code == 1


def test_cli_close_lineage(tmp_path: Path) -> None:
    from labs.ch03_proposals.cli import main

    planner, _ = plan_then_implement(
        "Adapter improves accuracy",
        "write adapter under adapters/v1/",
        metric="held_out_accuracy",
        paths=["adapters/v1/"],
        rollback_unit="adapters.v1",
        snapshot_ref="snap://adapters/v1@0",
        ownership_manifest=MANIFEST,
    )
    code = main(
        [
            "close-lineage",
            "--lineage-id",
            planner["lineage_id"],
            "--decision",
            "reject",
            "--reason",
            "lab refuse path",
        ]
    )
    assert code == 0
