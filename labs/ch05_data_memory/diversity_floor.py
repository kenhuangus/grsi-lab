"""Batch and corpus diversity floors for synthetic / experience keep decisions."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


@dataclass
class DiversityFloor:
    """Locked diversity floors declared before an overnight mutation."""

    min_unique_ngram_ratio: float = 0.55
    ngram_n: int = 5
    max_duplicate_fingerprint_ratio: float = 0.35
    min_tag_coverage: float = 0.5
    required_tags: set[str] = field(default_factory=set)
    max_self_similarity: float = 0.85


@dataclass
class DiversityReport:
    passed: bool
    reason: str
    unique_ngram_ratio: float
    duplicate_fingerprint_ratio: float
    tag_coverage: float
    self_similarity: float
    metrics: dict[str, Any] = field(default_factory=dict)


def _normalize_text(payload: Any) -> str:
    if isinstance(payload, str):
        text = payload
    elif isinstance(payload, dict):
        text = " ".join(str(v) for v in payload.values())
    else:
        text = str(payload)
    return " ".join(_TOKEN_RE.findall(text.lower()))


def _ngrams(text: str, n: int) -> list[str]:
    tokens = text.split()
    if len(tokens) < n:
        return tokens[:]
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def check_diversity_floor(
    batch: Iterable[dict[str, Any]],
    floor: DiversityFloor,
    *,
    incumbent: Iterable[dict[str, Any]] | None = None,
) -> DiversityReport:
    """Return pass/fail against ``floor`` for a candidate batch.

    Fail-closed: empty batches and missing payloads refuse.
    """
    records = list(batch)
    if not records:
        return DiversityReport(
            False,
            "empty batch",
            0.0,
            1.0,
            0.0,
            1.0,
        )

    texts: list[str] = []
    tags: set[str] = set()
    for rec in records:
        if "payload" not in rec:
            return DiversityReport(False, "missing payload", 0.0, 1.0, 0.0, 1.0)
        texts.append(_normalize_text(rec["payload"]))
        tags |= set(rec.get("tags") or [])

    all_ngrams: list[str] = []
    for text in texts:
        all_ngrams.extend(_ngrams(text, floor.ngram_n))
    unique_ratio = (len(set(all_ngrams)) / len(all_ngrams)) if all_ngrams else 0.0

    fps = [_fingerprint(t) for t in texts]
    fp_counts = Counter(fps)
    duplicate_ratio = sum(c - 1 for c in fp_counts.values()) / len(fps)

    if floor.required_tags:
        tag_coverage = len(tags & floor.required_tags) / len(floor.required_tags)
    else:
        tag_coverage = 1.0

    incumbent_texts = [_normalize_text(r["payload"]) for r in (incumbent or []) if "payload" in r]
    if incumbent_texts:
        batch_set = set()
        for t in texts:
            batch_set.update(_ngrams(t, floor.ngram_n))
        inc_set: set[str] = set()
        for t in incumbent_texts:
            inc_set.update(_ngrams(t, floor.ngram_n))
        self_similarity = _jaccard(batch_set, inc_set)
    else:
        # Within-batch collapse: mean pairwise fingerprint collision proxy
        self_similarity = duplicate_ratio

    if unique_ratio < floor.min_unique_ngram_ratio:
        return DiversityReport(
            False,
            "unique n-gram ratio below floor",
            unique_ratio,
            duplicate_ratio,
            tag_coverage,
            self_similarity,
        )
    if duplicate_ratio > floor.max_duplicate_fingerprint_ratio:
        return DiversityReport(
            False,
            "duplicate fingerprint ratio above ceiling",
            unique_ratio,
            duplicate_ratio,
            tag_coverage,
            self_similarity,
        )
    if tag_coverage < floor.min_tag_coverage:
        return DiversityReport(
            False,
            "held-out tag coverage below floor",
            unique_ratio,
            duplicate_ratio,
            tag_coverage,
            self_similarity,
        )
    if self_similarity > floor.max_self_similarity:
        return DiversityReport(
            False,
            "self-similarity / collapse above ceiling",
            unique_ratio,
            duplicate_ratio,
            tag_coverage,
            self_similarity,
        )

    return DiversityReport(
        True,
        "diversity floor cleared",
        unique_ratio,
        duplicate_ratio,
        tag_coverage,
        self_similarity,
        metrics={
            "batch_size": len(records),
            "unique_fingerprints": len(fp_counts),
            "tags_seen": sorted(tags),
        },
    )
