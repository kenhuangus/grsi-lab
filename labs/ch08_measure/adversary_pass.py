"""Adversary checks before held-out spend (gaming, locked paths, schema gaps)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from rsi_core.paths import normalize_lab_path
from rsi_core.schemas_load import validate_instance

_BLOCKED_PREFIXES = (
    "eval/",
    "evaluators/",
    "held_out/",
    "ledger/",
    "metric_cards/",
    "fixtures/datasets/",
    "fixtures/metric_cards/",
)

_ATTACK_PATTERNS = (
    re.compile(r"rewrite\s+evaluator", re.I),
    re.compile(r"bypass\s+held[- ]?out", re.I),
    re.compile(r"poison\s+metric", re.I),
    re.compile(r"exfiltrat", re.I),
)


@dataclass
class AdversaryFinding:
    """Result of adversary pass over a candidate."""

    passed: bool
    findings: list[str] = field(default_factory=list)


def adversary_pass(candidate: dict[str, Any]) -> AdversaryFinding:
    """Adversary checks for eval gaming / locked-path contact / schema gaps."""
    findings: list[str] = []
    try:
        validate_instance("candidate_diff", candidate)
    except Exception as exc:
        findings.append(f"candidate_diff schema invalid: {exc}")

    paths = (candidate.get("diff") or {}).get("paths") or []
    if not paths:
        findings.append("empty diff.paths")
    for path in paths:
        norm = normalize_lab_path(str(path))
        if norm.startswith(".."):
            findings.append(f"parent traversal in diff path: {path}")
        for prefix in _BLOCKED_PREFIXES:
            p = prefix.rstrip("/")
            if norm == p or norm.startswith(p + "/"):
                findings.append(f"path contacts evaluator surface: {path}")

    if not candidate.get("metric"):
        findings.append("missing metric")
    if not candidate.get("hypothesis"):
        findings.append("missing hypothesis")
    if not (candidate.get("rollback") or {}).get("unit"):
        findings.append("missing rollback.unit")

    hypothesis = str(candidate.get("hypothesis") or "")
    for pat in _ATTACK_PATTERNS:
        if pat.search(hypothesis):
            findings.append(f"hypothesis matches attack pattern: {pat.pattern}")

    return AdversaryFinding(passed=not findings, findings=findings)
