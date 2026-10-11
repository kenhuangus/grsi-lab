"""Token ROI gate for context-score / filter keep decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenROIGate:
    """Joint accuracy / token / latency band for a context-score candidate."""

    min_success_rate: float = 0.70
    max_mean_tokens: float = 4000.0
    max_p95_latency_ms: float = 2000.0
    require_token_improvement: bool = False
    baseline_mean_tokens: float | None = None
    blocked_context_tags: set[str] = field(default_factory=lambda: {"exfil", "eval_leak"})


@dataclass
class TokenROIResult:
    passed: bool
    reason: str
    success_rate: float
    mean_tokens: float
    p95_latency_ms: float
    details: dict[str, Any] = field(default_factory=dict)


def evaluate_token_roi(
    *,
    success_rate: float,
    mean_tokens: float,
    p95_latency_ms: float,
    gate: TokenROIGate,
    context_tags: set[str] | None = None,
) -> TokenROIResult:
    """Accept only when success holds and token/latency stay inside the band.

    Fail-closed on adversary-tagged notes reaching context and on success
    regression when tokens fall.
    """
    tags = set(context_tags or [])
    blocked = tags & gate.blocked_context_tags
    if blocked:
        return TokenROIResult(
            False,
            f"adversary tags reached context: {sorted(blocked)}",
            success_rate,
            mean_tokens,
            p95_latency_ms,
        )

    if success_rate < gate.min_success_rate:
        return TokenROIResult(
            False,
            "success rate below Token ROI floor",
            success_rate,
            mean_tokens,
            p95_latency_ms,
        )

    if mean_tokens > gate.max_mean_tokens:
        return TokenROIResult(
            False,
            "mean tokens above Token ROI ceiling",
            success_rate,
            mean_tokens,
            p95_latency_ms,
        )

    if p95_latency_ms > gate.max_p95_latency_ms:
        return TokenROIResult(
            False,
            "p95 latency above Token ROI ceiling",
            success_rate,
            mean_tokens,
            p95_latency_ms,
        )

    if gate.require_token_improvement:
        if gate.baseline_mean_tokens is None:
            return TokenROIResult(
                False,
                "missing baseline_mean_tokens for improvement check",
                success_rate,
                mean_tokens,
                p95_latency_ms,
            )
        if mean_tokens > gate.baseline_mean_tokens:
            return TokenROIResult(
                False,
                "mean tokens did not improve versus baseline",
                success_rate,
                mean_tokens,
                p95_latency_ms,
            )

    return TokenROIResult(
        True,
        "token roi cleared",
        success_rate,
        mean_tokens,
        p95_latency_ms,
        details={
            "min_success_rate": gate.min_success_rate,
            "max_mean_tokens": gate.max_mean_tokens,
            "max_p95_latency_ms": gate.max_p95_latency_ms,
        },
    )
