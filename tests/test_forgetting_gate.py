"""Forgetting gate with verified on-disk adapter artifacts."""

from __future__ import annotations

from pathlib import Path

from lab02_proposals_model.lora_candidate import forgetting_gate, make_adapter_candidate

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def test_forgetting_gate_fails_on_missing_post_scores(tmp_path: Path) -> None:
    env = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    result = forgetting_gate(env, {})
    assert result.passed is False
    assert "missing post scores" in result.message


def test_forgetting_gate_passes_when_scores_hold(tmp_path: Path) -> None:
    env = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    result = forgetting_gate(env, {"task_a": 0.79, "task_b": 0.74})
    assert result.passed is True


def test_forgetting_gate_detects_tampered_weights(tmp_path: Path) -> None:
    env = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    (tmp_path / "adapter" / "adapter_weights.bin").write_bytes(b"tampered")
    result = forgetting_gate(env, {"task_a": 0.79, "task_b": 0.74})
    assert result.passed is False
    assert "digest mismatch" in result.message


def test_forgetting_gate_rejects_regression_over_threshold(tmp_path: Path) -> None:
    env = make_adapter_candidate(LINEAGE, tmp_path / "adapter")
    env.forgetting_gate_threshold = 0.015
    result = forgetting_gate(env, {"task_a": 0.78, "task_b": 0.75})
    assert result.passed is False
    assert "prior-task regression" in result.message
    assert result.regressions["task_a"] > 0.015

