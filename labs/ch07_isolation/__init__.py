"""Chapter 7 lab — sandbox profiles, isolated runs, receipts, widening guards, probes."""

from labs.ch07_isolation.adversary_probes import ProbeResult, run_adversary_probes
from labs.ch07_isolation.receipts import IsolationReceipt, ReceiptStore, issue_receipt
from labs.ch07_isolation.run_isolated import IsolationRunResult, run_isolated
from labs.ch07_isolation.sandbox_profile import (
    DEFAULT_EVALUATOR_PATHS,
    SandboxViolation,
    assert_sandbox_allows,
    create_filesystem_jail,
    default_lab_profile,
    load_profile,
    materialize_candidate_paths,
    path_blocked,
    path_in_allowlist,
    resolve_in_jail,
)
from labs.ch07_isolation.widening_guard import WideningViolation, assert_no_widening

__all__ = [
    "DEFAULT_EVALUATOR_PATHS",
    "SandboxViolation",
    "assert_sandbox_allows",
    "create_filesystem_jail",
    "default_lab_profile",
    "load_profile",
    "materialize_candidate_paths",
    "path_blocked",
    "path_in_allowlist",
    "resolve_in_jail",
    "run_isolated",
    "IsolationRunResult",
    "IsolationReceipt",
    "ReceiptStore",
    "issue_receipt",
    "assert_no_widening",
    "WideningViolation",
    "run_adversary_probes",
    "ProbeResult",
]
