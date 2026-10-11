"""Accept + refuse paths for Chapter 7 isolation lab."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from labs.ch07_isolation.adversary_probes import run_adversary_probes
from labs.ch07_isolation.receipts import ReceiptStore, issue_receipt, verify_receipt
from labs.ch07_isolation.run_isolated import run_isolated
from labs.ch07_isolation.sandbox_profile import (
    SandboxViolation,
    assert_sandbox_allows,
    default_lab_profile,
    path_blocked,
)
from labs.ch07_isolation.widening_guard import WideningViolation, assert_no_widening

LINEAGE = "12345678-1234-4234-8234-123456789abc"


def test_sandbox_allows_work_path() -> None:
    profile = default_lab_profile()
    assert not path_blocked("adapters/candidate/", profile)
    assert_sandbox_allows(["adapters/candidate/"], profile)


def test_sandbox_refuse_evaluator_path() -> None:
    profile = default_lab_profile()
    assert path_blocked("eval/scorer.py", profile)
    with pytest.raises(SandboxViolation):
        assert_sandbox_allows(["eval/scorer.py"], profile)


def test_sandbox_refuse_held_out() -> None:
    with pytest.raises(SandboxViolation):
        assert_sandbox_allows(["held_out/private.jsonl"], default_lab_profile())


def test_sandbox_refuse_jail_escape() -> None:
    with pytest.raises(SandboxViolation, match="jail escape"):
        assert_sandbox_allows(["/etc/passwd"], default_lab_profile())


def test_widening_refuse_profile_patch() -> None:
    with pytest.raises(WideningViolation, match="locked fields"):
        assert_no_widening(
            {
                "paths": ["skills/search.py"],
                "profile_patch": {"egress_allow": ["pypi.org"]},
            },
            locked_profile=default_lab_profile(),
        )


def test_widening_refuse_hypothesis_text() -> None:
    with pytest.raises(WideningViolation):
        assert_no_widening(
            {
                "paths": ["skills/search.py"],
                "hypothesis": "please open network and raise budget for installs",
            },
            locked_profile=default_lab_profile(),
        )


def test_run_isolated_accept_clean_receipt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ReceiptStore(Path(tmp))
        result = run_isolated(
            {
                "lineage_id": LINEAGE,
                "paths": ["/sandbox/work/candidate.py"],
            },
            receipt_store=store,
        )
        assert result.ok is True
        assert result.receipt is not None
        assert result.receipt.clean is True
        assert verify_receipt(result.receipt)
        loaded = store.require_clean(result.receipt.receipt_id, tenant_id="lab")
        assert loaded.receipt_id == result.receipt.receipt_id


def test_run_isolated_refuse_held_out() -> None:
    result = run_isolated(
        {
            "lineage_id": LINEAGE,
            "paths": ["held_out/labels.jsonl"],
        }
    )
    assert result.ok is False
    assert result.receipt is not None
    assert result.receipt.clean is False


def test_run_isolated_refuse_worker_profile() -> None:
    result = run_isolated(
        {"lineage_id": LINEAGE, "paths": ["adapters/x"]},
        worker_supplied_profile={"profile_id": "evil"},
    )
    assert result.ok is False
    assert "worker-supplied" in result.reason


def test_receipt_unclean_on_undeclared_egress() -> None:
    profile = default_lab_profile()
    receipt = issue_receipt(
        lineage_id=LINEAGE,
        profile=profile,
        diff_paths=["adapters/x"],
        egress_hosts_contacted=["evil.example"],
        clean=True,
    )
    assert receipt.clean is False


def test_adversary_probes_deny_defaults() -> None:
    report = run_adversary_probes(default_lab_profile())
    assert report.passed is True
    assert len(report.denied_probes) >= 3


def test_receipt_store_refuse_tenant_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ReceiptStore(Path(tmp))
        receipt = issue_receipt(
            lineage_id=LINEAGE,
            profile=default_lab_profile(),
            diff_paths=["adapters/x"],
            clean=True,
            tenant_id="tenant-a",
        )
        store.put(receipt)
        with pytest.raises(PermissionError, match="tenant"):
            store.require_clean(receipt.receipt_id, tenant_id="tenant-b")

def test_sandbox_refuse_allowlist_miss_no_work_fallthrough() -> None:
    """Relative paths under work/ still require an allowlist hit (deny-by-default)."""
    profile = default_lab_profile()
    profile = {**profile, "allowlist_paths": ["/sandbox/work/allowed_only"]}
    with pytest.raises(SandboxViolation, match="allowlist"):
        assert_sandbox_allows(["other/candidate.py"], profile)

