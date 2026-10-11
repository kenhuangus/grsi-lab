"""Accept + refuse paths for Chapter 5 data/memory lab."""

from __future__ import annotations

import tempfile
from pathlib import Path

from labs.ch05_data_memory.admit_experience import AdmissionPolicy, admit_experience
from labs.ch05_data_memory.broker_client import ExperienceBroker
from labs.ch05_data_memory.diversity_floor import DiversityFloor, check_diversity_floor
from labs.ch05_data_memory.gvc_pipeline import GVCPipeline, default_gvc_validator
from labs.ch05_data_memory.token_roi_gate import TokenROIGate, evaluate_token_roi

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def _good_record(**extra: object) -> dict:
    base = {
        "lineage_id": LINEAGE,
        "payload": {
            "text": "inventory tool failed because schema field inventory_id was missing"
        },
        "quality": 0.9,
        "tags": ["tool_error"],
        "module_id": "planner",
    }
    base.update(extra)
    return base


def test_admit_accept_hashes_payload() -> None:
    result = admit_experience(_good_record(), AdmissionPolicy())
    assert result.admitted is True
    assert result.record is not None
    assert "payload_sha256" in result.record
    assert result.record["payload_entropy"] > 2.5


def test_admit_refuse_invalid_lineage() -> None:
    result = admit_experience(_good_record(lineage_id="x"), AdmissionPolicy())
    assert result.admitted is False
    assert "invalid lineage_id" in result.reason


def test_admit_refuse_missing_quality() -> None:
    rec = _good_record()
    del rec["quality"]
    result = admit_experience(rec, AdmissionPolicy())
    assert result.admitted is False
    assert "quality" in result.reason


def test_admit_refuse_eval_leak_tag() -> None:
    result = admit_experience(
        _good_record(tags=["eval_leak"]),
        AdmissionPolicy(),
    )
    assert result.admitted is False
    assert "blocked tags" in result.reason


def test_admit_refuse_leak_pattern_in_payload() -> None:
    result = admit_experience(
        _good_record(payload="copy held_out labels into the store"),
        AdmissionPolicy(),
    )
    assert result.admitted is False
    assert "leak pattern" in result.reason


def test_admit_refuse_low_entropy_collapse() -> None:
    result = admit_experience(
        _good_record(payload="aaaaaaaaaaaaaaaaaaaaaaaa"),
        AdmissionPolicy(min_entropy=2.5),
    )
    assert result.admitted is False
    assert "entropy" in result.reason


def test_diversity_accept_diverse_batch() -> None:
    floor = DiversityFloor(
        min_unique_ngram_ratio=0.4,
        max_duplicate_fingerprint_ratio=0.5,
        required_tags={"alpha", "beta"},
        min_tag_coverage=1.0,
        max_self_similarity=0.95,
    )
    batch = [
        {
            "payload": f"unique trajectory about retrieval cluster {i} with schema notes",
            "tags": ["alpha" if i % 2 == 0 else "beta"],
        }
        for i in range(5)
    ]
    report = check_diversity_floor(batch, floor)
    assert report.passed is True


def test_diversity_refuse_near_duplicates() -> None:
    floor = DiversityFloor(max_duplicate_fingerprint_ratio=0.1)
    batch = [
        {"payload": "same collapse template note", "tags": ["a"]},
        {"payload": "same collapse template note", "tags": ["a"]},
        {"payload": "same collapse template note", "tags": ["a"]},
    ]
    report = check_diversity_floor(batch, floor)
    assert report.passed is False


def test_token_roi_accept() -> None:
    result = evaluate_token_roi(
        success_rate=0.82,
        mean_tokens=1800,
        p95_latency_ms=900,
        gate=TokenROIGate(),
    )
    assert result.passed is True


def test_token_roi_refuse_success_drop() -> None:
    result = evaluate_token_roi(
        success_rate=0.4,
        mean_tokens=500,
        p95_latency_ms=100,
        gate=TokenROIGate(),
    )
    assert result.passed is False
    assert "success" in result.reason


def test_token_roi_refuse_adversary_tag() -> None:
    result = evaluate_token_roi(
        success_rate=0.9,
        mean_tokens=500,
        p95_latency_ms=100,
        gate=TokenROIGate(),
        context_tags={"eval_leak"},
    )
    assert result.passed is False
    assert "adversary" in result.reason


def test_gvc_refuse_when_diversity_fails() -> None:
    pipe = GVCPipeline(
        validator=default_gvc_validator,
        quality_floor=0.5,
        diversity_floor=DiversityFloor(max_duplicate_fingerprint_ratio=0.05),
    )
    batch = [
        {
            "lineage_id": LINEAGE,
            "payload": "identical synthetic note for collapse",
            "quality": 0.95,
            "tags": ["x"],
        }
        for _ in range(4)
    ]
    result = pipe.run(batch)
    assert result.kept is False
    assert result.diversity is not None
    assert result.diversity.passed is False


def test_gvc_accept() -> None:
    pipe = GVCPipeline(
        quality_floor=0.45,
        diversity_floor=DiversityFloor(
            max_duplicate_fingerprint_ratio=0.9,
            min_unique_ngram_ratio=0.2,
            max_self_similarity=0.99,
        ),
    )
    batch = [
        {
            "lineage_id": LINEAGE,
            "payload": {
                "text": (
                    f"inventory tool failed because schema field inventory_id "
                    f"was missing on retrieval path cluster {i}"
                )
            },
            # Client self-score must be ignored; independent validator decides.
            "quality": 0.01,
            "tags": ["tool_error", f"cluster_{i}"],
            "module_id": "planner",
        }
        for i in range(4)
    ]
    result = pipe.run(batch)
    assert result.kept is True
    assert result.corpus_root
    assert len(result.curated) >= 1
    assert all(rec["quality"] > 0.45 for rec in result.curated)
    assert all(rec.get("client_quality_ignored") == 0.01 for rec in result.curated)


def test_default_validator_ignores_client_quality() -> None:
    low_client = {
        "payload": {
            "text": "inventory tool failed because schema field inventory_id was missing"
        },
        "quality": 0.99,
    }
    empty = {"payload": "", "quality": 0.99}
    score = default_gvc_validator(low_client)
    assert 0.0 < score <= 1.0
    try:
        default_gvc_validator(empty)
        raised = False
    except ValueError:
        raised = True
    assert raised is True


def test_broker_admit_and_refuse() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        broker = ExperienceBroker(Path(tmp), policy=AdmissionPolicy(min_quality=0.5))
        ok = broker.admit_from_quarantine(_good_record())
        assert ok.admitted is True
        assert broker.current_count == 1
        bad = broker.admit_from_quarantine(_good_record(tags=["exfil"]))
        assert bad.admitted is False
        assert broker.current_count == 1
        assert any(a["event"] == "reject" for a in broker.list_audit())
