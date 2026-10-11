"""Generator–validator–curator pipeline for synthetic / experience batches."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from labs.ch05_data_memory.admit_experience import AdmissionPolicy, admit_experience
from labs.ch05_data_memory.diversity_floor import (
    DiversityFloor,
    DiversityReport,
    check_diversity_floor,
)

ValidatorFn = Callable[[dict[str, Any]], float]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _payload_text(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("text"), str):
            return payload["text"]
        return json.dumps(payload, sort_keys=True, default=str)
    if payload is None:
        return ""
    return str(payload)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def independent_quality_score(record: dict[str, Any]) -> float:
    """Compute quality from payload text only; never trust client score fields.

    Refuses client ``quality`` and client ``features.independent_score``.
    Raises ``ValueError`` when there is no independent text signal to score.
    """
    text = _payload_text(record).strip()
    # Explicitly ignore client-supplied numeric scores (including nested features).
    _ = record.get("quality")
    features = record.get("features")
    if isinstance(features, dict):
        _ = features.get("independent_score")

    if not text:
        raise ValueError("missing independent score: empty payload text")

    tokens = _TOKEN_RE.findall(text.lower())
    if len(tokens) < 4:
        raise ValueError("missing independent score: payload too short to score")

    entropy = _shannon_entropy(text)
    unique_ratio = len(set(tokens)) / len(tokens)
    length_factor = min(1.0, len(tokens) / 24.0)
    # Useful tool/schema language is a weak positive signal, not a client claim.
    keyword_hits = sum(
        1
        for kw in ("schema", "tool", "error", "inventory", "retriev", "field", "missing")
        if kw in text.lower()
    )
    keyword_factor = min(0.25, 0.05 * keyword_hits)
    score = 0.35 * min(1.0, entropy / 4.0) + 0.35 * unique_ratio + 0.25 * length_factor
    score += keyword_factor
    return max(0.0, min(1.0, score))


def default_gvc_validator(record: dict[str, Any]) -> float:
    """Default GVC validator: independent score only (ignores client quality)."""
    # Explicitly ignore client-supplied quality to prevent self-grading.
    _ = record.get("quality")
    return independent_quality_score(record)


@dataclass
class GVCResult:
    kept: bool
    reason: str
    curated: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    diversity: DiversityReport | None = None
    corpus_root: str | None = None


@dataclass
class GVCPipeline:
    """Run generate → validate → diversity → curate under locked floors."""

    validator: ValidatorFn = field(default=default_gvc_validator)
    quality_floor: float = 0.5
    admission_policy: AdmissionPolicy = field(default_factory=AdmissionPolicy)
    diversity_floor: DiversityFloor = field(default_factory=DiversityFloor)
    incumbent: list[dict[str, Any]] = field(default_factory=list)

    def run(self, candidates: list[dict[str, Any]]) -> GVCResult:
        """Validate, diversity-gate, then append-only curate survivors.

        The whole batch is discarded when the diversity floor fails, even if
        per-record validator scores clear the quality floor. Client-supplied
        ``quality`` is overwritten by the validator score.
        """
        if not candidates:
            return GVCResult(False, "empty candidate batch")

        scored: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for raw in candidates:
            record = dict(raw)
            client_quality = record.pop("quality", None)
            try:
                score = float(self.validator(record))
            except Exception as exc:  # noqa: BLE001 — validator bugs refuse the record
                rejected.append(
                    {
                        **record,
                        "reject_reason": f"validator error: {exc}",
                        "client_quality_ignored": client_quality,
                    }
                )
                continue
            record["quality"] = score
            if client_quality is not None:
                record["client_quality_ignored"] = float(client_quality)
            if score < self.quality_floor:
                rejected.append({**record, "reject_reason": "quality below validator floor"})
                continue
            scored.append(record)

        if not scored:
            return GVCResult(False, "no records cleared validator floor", rejected=rejected)

        diversity = check_diversity_floor(
            scored,
            self.diversity_floor,
            incumbent=self.incumbent,
        )
        if not diversity.passed:
            for rec in scored:
                rejected.append({**rec, "reject_reason": diversity.reason})
            return GVCResult(
                False,
                diversity.reason,
                rejected=rejected,
                diversity=diversity,
            )

        curated: list[dict[str, Any]] = []
        for rec in scored:
            result = admit_experience(
                rec,
                self.admission_policy,
                current_count=len(self.incumbent) + len(curated),
            )
            if not result.admitted or result.record is None:
                rejected.append({**rec, "reject_reason": result.reason})
                continue
            curated.append(result.record)

        if not curated:
            return GVCResult(
                False,
                "admission refused all diversity survivors",
                rejected=rejected,
                diversity=diversity,
            )

        root_material = json.dumps(
            [r["payload_sha256"] for r in curated],
            sort_keys=True,
        ).encode("utf-8")
        corpus_root = hashlib.blake2b(root_material, digest_size=16).hexdigest()
        return GVCResult(
            True,
            "gvc curated batch",
            curated=curated,
            rejected=rejected,
            diversity=diversity,
            corpus_root=corpus_root,
        )
