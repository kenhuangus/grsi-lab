"""Lab 04 (legacy) — re-exports Chapter 7 isolation + Chapter 8 measure."""

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
)
from labs.ch08_measure.adversary_pass import AdversaryFinding, adversary_pass
from labs.ch08_measure.evaluate_keep import evaluate_keep, require_isolation_receipt
from labs.ch08_measure.ledger import GENESIS, SealedLedger, hash_entry
from labs.ch08_measure.metric_card import EvalBundle, evaluate_metric_card, load_metric_card

__all__ = [
    "DEFAULT_EVALUATOR_PATHS",
    "AdversaryFinding",
    "EvalBundle",
    "GENESIS",
    "IsolationReceipt",
    "IsolationRunResult",
    "ReceiptStore",
    "SandboxViolation",
    "SealedLedger",
    "adversary_pass",
    "assert_sandbox_allows",
    "create_filesystem_jail",
    "default_lab_profile",
    "evaluate_keep",
    "evaluate_metric_card",
    "hash_entry",
    "issue_receipt",
    "load_metric_card",
    "load_profile",
    "materialize_candidate_paths",
    "path_blocked",
    "require_isolation_receipt",
    "run_isolated",
]
