"""External evaluator: adversary checks, metric-card scoring, sealed ledger."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lab04_isolation_eval.metric_eval import EvalBundle, evaluate_metric_card, load_metric_card
from rsi_core.durable_store import DurableStore
from rsi_core.paths import normalize_lab_path
from rsi_core.schemas_load import validate_instance

GENESIS = "GENESIS"

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


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_entry(prev_hash: str, payload: dict[str, Any]) -> str:
    """Compute SHA-256 entry hash chained from ``prev_hash``."""
    material = prev_hash.encode("utf-8") + _canonical(payload)
    return hashlib.sha256(material).hexdigest()


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


@dataclass
class SealedLedger:
    """Hash-chained sealed decision ledger (memory + optional SQLite durability)."""

    entries: list[dict[str, Any]] = field(default_factory=list)
    store: DurableStore | None = None

    def __post_init__(self) -> None:
        if self.store is not None and not self.entries:
            self.entries = self.store.list_sealed()

    @property
    def tip_hash(self) -> str:
        if not self.entries:
            return GENESIS
        return str(self.entries[-1]["entry_hash"])

    def seal(
        self,
        *,
        lineage_id: str,
        decision: str,
        metric_card_id: str,
        repro_script: str,
        scores: dict[str, float] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Append a schema-valid sealed_decision with hash chain linkage."""
        prev = self.tip_hash
        payload = {
            "lineage_id": lineage_id,
            "decision": decision,
            "score_authority": "external_evaluator",
            "metric_card_id": metric_card_id,
            "scores": scores or {},
            "repro_script": repro_script,
            "notes": notes or "",
        }
        entry_hash = hash_entry(prev, payload)
        sealed = {
            **payload,
            "prev_hash": prev,
            "entry_hash": entry_hash,
        }
        if not sealed["notes"]:
            del sealed["notes"]
        if not sealed["scores"]:
            del sealed["scores"]
        validated = validate_instance("sealed_decision", sealed)
        self.entries.append(validated)
        if self.store is not None:
            self.store.append_sealed(validated)
        return validated

    def verify_chain(self) -> bool:
        """Recompute hashes; return True if the chain is intact."""
        prev = GENESIS
        for entry in self.entries:
            payload = {
                k: entry[k]
                for k in (
                    "lineage_id",
                    "decision",
                    "score_authority",
                    "metric_card_id",
                    "scores",
                    "repro_script",
                    "notes",
                )
                if k in entry
            }
            if "scores" not in payload:
                payload["scores"] = {}
            if "notes" not in payload:
                payload["notes"] = ""
            expected = hash_entry(prev, payload)
            if entry.get("prev_hash") != prev or entry.get("entry_hash") != expected:
                return False
            prev = entry["entry_hash"]
        return True


def evaluate_keep(
    candidate: dict[str, Any],
    ledger: SealedLedger,
    *,
    metric_card: dict[str, Any] | None = None,
    metric_card_path: str | Path | None = None,
    dataset_root: str | Path | None = None,
    repro_script: str = "running_lab/repro.py",
    keep_threshold: float = 0.5,
    ablation_module_scores: dict[str, float] | None = None,
    tokens_used: float = 1000.0,
) -> dict[str, Any]:
    """Run adversary pass + metric-card evaluation, then seal keep/revert/reject.

    Scores are measured from on-disk datasets referenced by the metric card.
    Callers may not inject a held-out score.
    """
    adv = adversary_pass(candidate)
    card_id = "lab-metric-card"
    if metric_card is not None:
        card = validate_instance("metric_card", metric_card)
        card_id = card["card_id"]
    elif metric_card_path is not None:
        card = load_metric_card(metric_card_path)
        card_id = card["card_id"]
    else:
        # Default lab card next to package fixtures
        root = Path(__file__).resolve().parents[1]
        card = load_metric_card(root / "fixtures" / "metric_cards" / "lab_metric_card.json")
        card_id = card["card_id"]

    if dataset_root is None:
        dataset_root = Path(__file__).resolve().parents[1] / "fixtures" / "datasets"

    if not adv.passed:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores={"held_out": 0.0, "held_in": 0.0, "token_roi": 0.0},
            notes="; ".join(adv.findings),
        )

    bundle: EvalBundle = evaluate_metric_card(
        card,
        dataset_root=dataset_root,
        ablation_module_scores=ablation_module_scores
        or {"adapter": float(keep_threshold) - 0.01},
        tokens_used=tokens_used,
    )
    if not bundle.ablation_ok:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores=bundle.scores,
            notes="module ablation failed",
        )

    decision = "keep" if bundle.scores["held_out"] >= keep_threshold else "revert"
    return ledger.seal(
        lineage_id=candidate["lineage_id"],
        decision=decision,
        metric_card_id=card_id,
        repro_script=repro_script,
        scores=bundle.scores,
        notes=json.dumps(
            {
                "seeds": bundle.details.get("seeds"),
                "aggregate": bundle.details.get("aggregate"),
            }
        ),
    )
