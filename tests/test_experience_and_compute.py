"""Experience admission and compute budget real gates."""

from __future__ import annotations

import pytest
from jsonschema.exceptions import ValidationError

from lab03_data_orchestration.experience_admission import AdmissionPolicy, admit_experience
from rsi_core.compute_budget import ComputeBudgetError, ComputeBudgetLedger

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def test_admit_requires_quality() -> None:
    result = admit_experience(
        {"lineage_id": LINEAGE, "payload": {"text": "ok"}},
        AdmissionPolicy(),
    )
    assert result.admitted is False
    assert "quality" in result.reason


def test_admit_hashes_payload() -> None:
    result = admit_experience(
        {"lineage_id": LINEAGE, "payload": {"text": "ok"}, "quality": 0.9},
        AdmissionPolicy(),
    )
    assert result.admitted is True
    assert "payload_sha256" in result.record


def test_admit_blocks_eval_leak_payload() -> None:
    result = admit_experience(
        {
            "lineage_id": LINEAGE,
            "payload": "leak held_out labels",
            "quality": 1.0,
        },
        AdmissionPolicy(),
    )
    assert result.admitted is False


def test_compute_budget_rejects_unscoped() -> None:
    ledger = ComputeBudgetLedger()
    with pytest.raises(ValidationError):
        ledger.validate_request(
            {
                "lineage_id": LINEAGE,
                "budget": {"units": "wall_seconds", "amount": 0},
                "target_metric": "x",
                "stop_rule": "none",
            }
        )


def test_compute_budget_authorizes_spend() -> None:
    ledger = ComputeBudgetLedger()
    out = ledger.authorize_spend(
        {
            "lineage_id": LINEAGE,
            "budget": {"units": "tokens", "amount": 100},
            "target_metric": "held_out",
            "stop_rule": "wall",
        },
        amount=50,
    )
    assert out["status"] == "authorized"
    with pytest.raises(ComputeBudgetError):
        ledger.authorize_spend(
            {
                "lineage_id": LINEAGE,
                "budget": {"units": "tokens", "amount": 100},
                "target_metric": "held_out",
                "stop_rule": "wall",
            },
            amount=200,
        )
