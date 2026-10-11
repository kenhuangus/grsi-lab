"""Evidence pack assembled from sealed keep + freeze scan for human promote review."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_evidence_pack(
    *,
    sealed_decision: dict[str, Any],
    scan_report: dict[str, Any],
    candidate: dict[str, Any],
    metric_card_id: str | None = None,
) -> dict[str, Any]:
    """Build a content-addressed evidence pack for promotion reviewers."""
    if sealed_decision.get("decision") != "keep":
        raise ValueError("evidence pack requires sealed decision=keep")
    if not scan_report.get("passed"):
        raise ValueError("evidence pack requires passed frozen-policy scan")

    receipt = candidate.get("isolation_receipt") or {}
    pack = {
        "lineage_id": sealed_decision["lineage_id"],
        "entry_hash": sealed_decision["entry_hash"],
        "prev_hash": sealed_decision.get("prev_hash"),
        "metric_card_id": metric_card_id or sealed_decision.get("metric_card_id"),
        "scores": sealed_decision.get("scores") or {},
        "repro_script": sealed_decision.get("repro_script"),
        "isolation_receipt_id": receipt.get("receipt_id"),
        "scan_report_hash": scan_report["report_hash"],
        "candidate_paths": list((candidate.get("diff") or {}).get("paths") or []),
        "score_authority": sealed_decision.get("score_authority"),
    }
    pack["pack_hash"] = hashlib.sha256(_canonical(pack)).hexdigest()
    return pack


def verify_evidence_pack(pack: dict[str, Any]) -> bool:
    """Recompute ``pack_hash``; return True if intact."""
    body = {k: v for k, v in pack.items() if k != "pack_hash"}
    expected = hashlib.sha256(_canonical(body)).hexdigest()
    return pack.get("pack_hash") == expected
