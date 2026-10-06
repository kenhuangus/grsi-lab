"""Tests for sealed decision hash chain."""

from __future__ import annotations

from lab04_isolation_eval.eval_service import SealedLedger, hash_entry


def test_sealed_decision_hash_chain() -> None:
    ledger = SealedLedger()
    e1 = ledger.seal(
        lineage_id="12345678-1234-4234-8234-123456789abc",
        decision="keep",
        metric_card_id="card-1",
        repro_script="scripts/repro.py",
        scores={"held_out": 0.8},
    )
    assert e1["prev_hash"] == "GENESIS"
    assert len(e1["entry_hash"]) == 64

    e2 = ledger.seal(
        lineage_id="12345678-1234-4234-8234-123456789abd",
        decision="revert",
        metric_card_id="card-1",
        repro_script="scripts/repro.py",
        scores={"held_out": 0.4},
    )
    assert e2["prev_hash"] == e1["entry_hash"]
    assert ledger.verify_chain() is True


def test_tampered_chain_fails_verify() -> None:
    ledger = SealedLedger()
    ledger.seal(
        lineage_id="12345678-1234-4234-8234-123456789abc",
        decision="keep",
        metric_card_id="card-1",
        repro_script="scripts/repro.py",
    )
    ledger.entries[0]["entry_hash"] = "0" * 64
    assert ledger.verify_chain() is False


def test_hash_entry_deterministic() -> None:
    payload = {
        "lineage_id": "12345678-1234-4234-8234-123456789abc",
        "decision": "reject",
        "score_authority": "external_evaluator",
        "metric_card_id": "c",
        "scores": {},
        "repro_script": "r.py",
        "notes": "",
    }
    assert hash_entry("GENESIS", payload) == hash_entry("GENESIS", payload)
