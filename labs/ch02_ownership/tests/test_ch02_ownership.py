"""Accept + refuse paths for Chapter 2 ownership lab."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from labs.ch02_ownership.blast_radius import assess_blast_radius
from labs.ch02_ownership.freeze_gate import FREEZE_CHECKLIST_ITEMS, FreezeStatus, run_freeze_gate
from labs.ch02_ownership.manifest import validate_modularity
from labs.ch02_ownership.reject_locked_writes import assert_paths_writable, inspect_writes
from rsi_core.types import LockedPathError

MANIFEST = {
    "version": "1.0",
    "components": [
        {
            "path": "harness/skills/",
            "owner": "platform",
            "eval_hook": "eval/hooks/skill_heldout.py",
            "rollback_unit": "harness.skills",
            "observability_signal": "skill_ablation_delta",
            "surface": "orchestration",
        },
        {
            "path": "adapters/",
            "owner": "ml",
            "eval_hook": "eval/hooks/adapter_heldout.py",
            "rollback_unit": "adapters.candidate",
            "observability_signal": "forgetting_gate",
            "surface": "model",
        },
    ],
    "locked": [
        "eval/",
        "evaluators/",
        "held_out/",
        "metric_cards/",
        "ledger/",
        "sandbox/",
        "promotion/",
        "safety/",
        "ownership/",
        "schemas/",
        "CONTRACTS.md",
    ],
}

ORCH_EVIDENCE = {
    "held_out_task_metric": "fixtures/datasets/held_out.jsonl",
    "module_ablation": "fixtures/ablation/planner.json",
    "single_reload_boundary": {"path": "harness/schema/v1.json", "ref": "schema"},
}


def test_accept_declared_mutable_write() -> None:
    """Accept path: declared harness write under modularity + ownership."""
    report = inspect_writes(["harness/skills/planner.py"], MANIFEST, require_declared=True)
    assert report.accepted is True
    assert report.rejects == []
    assert_paths_writable(["harness/skills/planner.py"], MANIFEST, require_declared=True)


def test_refuse_locked_path() -> None:
    with pytest.raises(LockedPathError) as exc:
        assert_paths_writable(["eval/scorer.py"], MANIFEST, require_declared=True)
    assert "locked" in str(exc.value).lower()


def test_refuse_undeclared_path() -> None:
    report = inspect_writes(["memory/rules/admit.yaml"], MANIFEST, require_declared=True)
    assert report.accepted is False
    assert report.rejects[0].reject_class == "undeclared_path"


def test_refuse_parent_traversal() -> None:
    report = inspect_writes(
        ["work/../../eval/scorer.py"], MANIFEST, require_declared=True
    )
    assert report.accepted is False
    assert report.rejects[0].reject_class == "parent_traversal"
    with pytest.raises(LockedPathError):
        assert_paths_writable(
            ["work/../../eval/scorer.py"], MANIFEST, require_declared=True
        )


def test_refuse_component_overlapping_locked() -> None:
    bad = {
        "version": "1.0",
        "components": [
            {
                "path": "eval/external/",
                "owner": "lab",
                "eval_hook": "hook",
                "rollback_unit": "r",
                "observability_signal": "o",
            }
        ],
        "locked": ["eval/"],
    }
    errors = validate_modularity(bad)
    assert any("overlaps locked" in e for e in errors)


def test_freeze_gate_refuse_bare_boolean_evidence(tmp_path: Path) -> None:
    """Bare checklist True without evidence_paths must not pass."""
    evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    result = run_freeze_gate(MANIFEST, evidence=evidence)
    assert result.passed is False
    assert result.status is FreezeStatus.FAILED
    assert any("without evidence path" in f for f in result.failures)


def test_freeze_gate_accept_with_full_evidence(tmp_path: Path) -> None:
    artifact = tmp_path / "freeze_evidence.json"
    payload = b'{"ok":true}'
    artifact.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    evidence_paths = {
        item: {"path": str(artifact), "sha256": digest}
        for item in FREEZE_CHECKLIST_ITEMS
        if item
        not in {"ownership_manifest_locked", "safety_constitution_locked"}
    }
    result = run_freeze_gate(
        MANIFEST, evidence=evidence, evidence_paths=evidence_paths
    )
    assert result.passed is True
    assert result.status is FreezeStatus.PASSED


def test_freeze_gate_refuse_incomplete_checklist() -> None:
    result = run_freeze_gate(MANIFEST, evidence={})
    assert result.passed is False
    assert result.status is FreezeStatus.FAILED
    assert any("checklist unmet" in f for f in result.failures)


def test_freeze_gate_refuse_missing_prefix(tmp_path: Path) -> None:
    incomplete = {
        **MANIFEST,
        "locked": ["eval/", "held_out/", "metric_cards/", "ledger/", "ownership/"],
    }
    artifact = tmp_path / "freeze_evidence.json"
    artifact.write_text("{}", encoding="utf-8")
    evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    evidence_paths = {
        item: str(artifact)
        for item in FREEZE_CHECKLIST_ITEMS
        if item
        not in {"ownership_manifest_locked", "safety_constitution_locked"}
    }
    result = run_freeze_gate(
        incomplete, evidence=evidence, evidence_paths=evidence_paths
    )
    assert result.passed is False
    assert result.status is FreezeStatus.FAILED
    assert any("locked coverage incomplete" in f for f in result.failures)


def test_freeze_gate_break_open(tmp_path: Path) -> None:
    artifact = tmp_path / "freeze_evidence.json"
    artifact.write_text("{}", encoding="utf-8")
    evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    evidence_paths = {
        item: str(artifact)
        for item in FREEZE_CHECKLIST_ITEMS
        if item
        not in {"ownership_manifest_locked", "safety_constitution_locked"}
    }
    result = run_freeze_gate(
        MANIFEST,
        evidence=evidence,
        evidence_paths=evidence_paths,
        break_ticket="TICKET-1",
        break_paths=["safety/constitution.md"],
    )
    assert result.passed is False
    assert result.status is FreezeStatus.BREAK_OPEN
    assert result.break_ticket == "TICKET-1"


def test_freeze_gate_evidence_paths_verify_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "metric_card.json"
    payload = b'{"metric":"held_out"}'
    artifact.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    evidence = {item: True for item in FREEZE_CHECKLIST_ITEMS}
    evidence_paths = {
        "metric_card_registered": {"path": str(artifact), "sha256": digest},
    }
    # Missing paths for other True claims → refuse (do not trust bare booleans alone).
    result = run_freeze_gate(
        MANIFEST, evidence=evidence, evidence_paths=evidence_paths
    )
    assert result.passed is False
    assert any("without evidence path" in f for f in result.failures)

    # Wrong hash refuses even when boolean is True.
    evidence_paths_bad = {
        item: {"path": str(artifact), "sha256": "0" * 64}
        for item in FREEZE_CHECKLIST_ITEMS
    }
    result_bad = run_freeze_gate(
        MANIFEST, evidence=evidence, evidence_paths=evidence_paths_bad
    )
    assert result_bad.passed is False
    assert any("hash mismatch" in f for f in result_bad.failures)

    # Full path coverage with matching hashes accepts.
    evidence_paths_ok = {
        item: {"path": str(artifact), "sha256": digest}
        for item in FREEZE_CHECKLIST_ITEMS
    }
    result_ok = run_freeze_gate(
        MANIFEST, evidence=evidence, evidence_paths=evidence_paths_ok
    )
    assert result_ok.passed is True


def test_blast_refuse_cross_surface() -> None:
    assessment = assess_blast_radius(
        ["harness/skills/planner.py", "adapters/v1/"],
        MANIFEST,
        evidence=ORCH_EVIDENCE,
    )
    assert assessment.accepted is False
    assert assessment.undeclared_cross_surface is True


def test_blast_refuse_bare_boolean_evidence() -> None:
    assessment = assess_blast_radius(
        ["harness/skills/planner.py"],
        MANIFEST,
        declared_surface="orchestration",
        evidence={
            "held_out_task_metric": True,
            "module_ablation": True,
            "single_reload_boundary": True,
        },
    )
    assert assessment.accepted is False
    assert any("missing required evidence" in r for r in assessment.refusals)


def test_blast_refuse_infrastructure() -> None:
    assessment = assess_blast_radius(
        ["sandbox/profile.yaml"],
        MANIFEST,
        evidence={
            "escape_test": "probes/escape.json",
            "egress_probe": "probes/egress.json",
            "credential_ttl_check": "probes/ttl.json",
            "change_control_ticket": "tickets/CHG-1",
        },
    )
    assert assessment.accepted is False
    assert assessment.infrastructure_touch is True
    assert any("infrastructure" in r for r in assessment.refusals)


def test_blast_refuse_missing_evidence() -> None:
    assessment = assess_blast_radius(
        ["harness/skills/planner.py"],
        MANIFEST,
        declared_surface="orchestration",
        evidence={},
    )
    assert assessment.accepted is False
    assert any("missing required evidence" in r for r in assessment.refusals)


def test_blast_accept_single_surface() -> None:
    assessment = assess_blast_radius(
        ["harness/skills/planner.py"],
        MANIFEST,
        declared_surface="orchestration",
        evidence=ORCH_EVIDENCE,
    )
    assert assessment.accepted is True
    assert assessment.primary_surface == "orchestration"


def test_cli_reject_locked(tmp_path: Path) -> None:
    from labs.ch02_ownership.cli import main

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    code = main(["reject", "--manifest", str(manifest_path), "eval/scorer.py"])
    assert code == 1


def test_cli_freeze_requires_evidence(tmp_path: Path) -> None:
    from labs.ch02_ownership.cli import main

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    code = main(["freeze", "--manifest", str(manifest_path)])
    assert code == 1
