"""Accept + refuse paths for Chapter 4 model-surface lab."""

from __future__ import annotations

from pathlib import Path

import pytest

from labs.ch03_proposals.lineage import (
    close_proposal_lineage,
    open_proposal_lineage,
    reset_registry,
)
from labs.ch04_model_surface.adapter_package import make_adapter_candidate
from labs.ch04_model_surface.cheapest_surface import CheaperAttempt, require_cheapest_surface
from labs.ch04_model_surface.forgetting_gate import forgetting_gate
from labs.ch04_model_surface.recipe_contract import (
    RecipeContractError,
    assert_recipe_unchanged,
    build_recipe_contract,
)
from labs.ch04_model_surface.train_job_record import TrainJobError, open_train_job

LINEAGE = "12345678-1234-4234-8234-123456789abc"
FAKE_LINEAGE = "12345678-1234-4234-8234-123456789abd"


@pytest.fixture(autouse=True)
def _clean_lineage_registry() -> None:
    reset_registry()
    yield
    reset_registry()


def _closed_cheaper_lineage(
    *,
    metric: str = "held_out_accuracy",
    surface: str = "orchestration",
) -> str:
    record = open_proposal_lineage(role="implementer", surface=surface, metric=metric)
    close_proposal_lineage(record.lineage_id, "revert", reason="failed_min_delta")
    return record.lineage_id


def test_accept_adapter_and_forgetting_gate(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    result = forgetting_gate(package, {"task_a": 0.79, "task_b": 0.74})
    assert result.passed is True
    assert package.weights_sha256
    assert len(package.weights_sha256) == 64


def test_refuse_adapter_invalid_lineage(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid lineage_id"):
        make_adapter_candidate("not-a-uuid", tmp_path / "adapter")


def test_refuse_forgetting_missing_post_scores(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    result = forgetting_gate(package, {})
    assert result.passed is False
    assert "missing post scores" in result.message


def test_refuse_forgetting_regression(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    package.forgetting_gate_threshold = 0.015
    result = forgetting_gate(package, {"task_a": 0.78, "task_b": 0.75})
    assert result.passed is False
    assert "prior-task regression" in result.message


def test_refuse_tampered_weights(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    (tmp_path / "adapter" / "adapter_weights.bin").write_bytes(b"tampered")
    result = forgetting_gate(package, {"task_a": 0.79, "task_b": 0.74})
    assert result.passed is False
    assert "digest mismatch" in result.message


def test_refuse_cheapest_surface_without_evidence() -> None:
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold",
        cheaper_attempts=[],
        harness_candidates=["harness/skills/planner.py"],
        experience_candidates=[],
    )
    assert decision.allowed is False
    assert any("cheaper-surface lineage" in r for r in decision.refusals)


def test_refuse_cheapest_surface_empty_candidates() -> None:
    cheaper = _closed_cheaper_lineage()
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold on planner skill",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id=cheaper,
                surface="orchestration",
                metric="held_out_accuracy",
                outcome="failed_min_delta",
            )
        ],
        harness_candidates=[],
        experience_candidates=[],
    )
    assert decision.allowed is False
    assert any("non-empty" in r for r in decision.refusals)


def test_refuse_cheapest_surface_fake_lineage() -> None:
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold on planner skill",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id=FAKE_LINEAGE,
                surface="orchestration",
                metric="held_out_accuracy",
                outcome="failed_min_delta",
            )
        ],
        harness_candidates=["harness/skills/planner.py"],
    )
    assert decision.allowed is False
    assert any("not in registry" in r or "self-attested" in r for r in decision.refusals)


def test_refuse_cheapest_surface_boolean_listed_not_evidence() -> None:
    cheaper = _closed_cheaper_lineage()
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold on planner skill",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id=cheaper,
                surface="orchestration",
                metric="held_out_accuracy",
                outcome="failed_min_delta",
            )
        ],
        harness_candidates_listed=True,
        experience_candidates_listed=False,
    )
    assert decision.allowed is False
    assert any("not evidence" in r or "non-empty" in r for r in decision.refusals)


def test_accept_cheapest_surface_with_lineage() -> None:
    cheaper = _closed_cheaper_lineage()
    decision = require_cheapest_surface(
        metric="held_out_accuracy",
        failure_statement="held_out_accuracy below card threshold on planner skill",
        cheaper_attempts=[
            CheaperAttempt(
                lineage_id=cheaper,
                surface="orchestration",
                metric="held_out_accuracy",
                outcome="failed_min_delta",
            )
        ],
        harness_candidates=["harness/skills/planner.py"],
        experience_candidates=[],
    )
    assert decision.allowed is True


def test_refuse_dpo_recipe_without_judge() -> None:
    with pytest.raises(RecipeContractError):
        build_recipe_contract(
            lineage_id=LINEAGE,
            kind="dpo",
            data_mix_id="mix-v1",
            loss_name="dpo",
            schedule="cosine",
            stop_rule="steps=1000",
            preference_source="prefs-v1",
            judge_ref=None,
        )


def test_refuse_recipe_drift() -> None:
    pinned = build_recipe_contract(
        lineage_id=LINEAGE,
        kind="sft",
        data_mix_id="mix-v1",
        loss_name="ce",
        schedule="cosine",
        stop_rule="steps=1000",
    )
    drifted = build_recipe_contract(
        lineage_id=LINEAGE,
        kind="sft",
        data_mix_id="mix-v2",
        loss_name="ce",
        schedule="cosine",
        stop_rule="steps=1000",
    )
    with pytest.raises(RecipeContractError):
        assert_recipe_unchanged(pinned, drifted)


def test_refuse_train_job_without_metric_card(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    recipe = build_recipe_contract(
        lineage_id=LINEAGE,
        kind="sft",
        data_mix_id="mix-v1",
        loss_name="ce",
        schedule="cosine",
        stop_rule="steps=1000",
    )
    with pytest.raises(TrainJobError):
        open_train_job(
            package=package,
            recipe=recipe,
            metric_card_id="",
            metric_card_sha256="a" * 64,
            sandbox_profile_id="lab-default",
        )


def test_accept_train_job(tmp_path: Path) -> None:
    package = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    recipe = build_recipe_contract(
        lineage_id=LINEAGE,
        kind="sft",
        data_mix_id="mix-v1",
        loss_name="ce",
        schedule="cosine",
        stop_rule="steps=1000",
    )
    job = open_train_job(
        package=package,
        recipe=recipe,
        metric_card_id="card-v1",
        metric_card_sha256="b" * 64,
        sandbox_profile_id="lab-default",
    )
    assert job.status == "queued"
    assert job.lineage_id == LINEAGE
