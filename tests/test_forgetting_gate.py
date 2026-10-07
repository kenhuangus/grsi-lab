"""Forgetting gate fail-closed behavior."""

from __future__ import annotations

from lab02_proposals_model.lora_candidate import forgetting_gate, make_stub_lora


def test_forgetting_gate_fails_on_missing_post_scores() -> None:
    env = make_stub_lora("12345678-1234-4234-8234-123456789abc")
    result = forgetting_gate(env, {})
    assert result.passed is False
    assert "missing post scores" in result.message


def test_forgetting_gate_passes_when_scores_hold() -> None:
    env = make_stub_lora("12345678-1234-4234-8234-123456789abc")
    result = forgetting_gate(env, {"task_a": 0.79, "task_b": 0.74})
    assert result.passed is True
