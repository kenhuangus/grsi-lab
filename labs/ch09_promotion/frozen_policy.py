"""Frozen-policy scan — real checks against ownership manifests and candidates."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from rsi_core.ownership import is_locked
from rsi_core.paths import normalize_lab_path


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_frozen_policy_scan(
    *,
    candidate: dict[str, Any],
    ownership_manifest: dict[str, Any],
    sealed_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scan candidate/decision against Last Frozen Layer ownership rules.

    Returns a report with ``passed`` and ``report_hash`` (SHA-256 of canonical JSON).
    """
    findings: list[str] = []
    paths = list((candidate.get("diff") or {}).get("paths") or [])
    for path in paths:
        if is_locked(path, ownership_manifest):
            findings.append(f"candidate touches locked path: {normalize_lab_path(path)}")

    locked = ownership_manifest.get("locked") or []
    if not locked:
        findings.append("ownership manifest has empty locked set")

    if sealed_decision is not None:
        if sealed_decision.get("decision") != "keep":
            findings.append("sealed decision is not keep")
        if sealed_decision.get("score_authority") != "external_evaluator":
            findings.append("score authority is not external_evaluator")

    report = {
        "passed": not findings,
        "findings": findings,
        "paths_scanned": [normalize_lab_path(p) for p in paths],
        "locked_prefixes": [normalize_lab_path(str(p)) for p in locked],
        "lineage_id": candidate.get("lineage_id"),
    }
    report["report_hash"] = hashlib.sha256(_canonical(report)).hexdigest()
    return report
