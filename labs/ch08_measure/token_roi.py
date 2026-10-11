"""Token ROI measurement and authorize-gate helpers."""

from __future__ import annotations

import math
from typing import Any


def compute_token_roi(*, utility_gain: float, tokens_used: float) -> float:
    """Return utility_gain / tokens_used; refuse non-finite results."""
    denom = max(float(tokens_used), 1e-9)
    roi = float(utility_gain) / denom
    if not math.isfinite(roi):
        raise ValueError("token_roi not finite")
    return roi


def gate_token_roi(
    *,
    held_out: float,
    tokens_used: float,
    min_roi: float,
    utility_gain: float | None = None,
) -> dict[str, Any]:
    """Authorize when measured Token ROI meets ``min_roi``; else refuse.

    Numerator defaults to held-out score (lab card convention). Callers may
    pass an explicit ``utility_gain`` (e.g. held-out delta) when available.
    """
    gain = float(held_out) if utility_gain is None else float(utility_gain)
    roi = compute_token_roi(utility_gain=gain, tokens_used=tokens_used)
    passed = roi >= float(min_roi)
    return {
        "passed": passed,
        "token_roi": roi,
        "min_roi": float(min_roi),
        "utility_gain": gain,
        "tokens_used": float(tokens_used),
        "reason": None if passed else f"token_roi {roi} below min_roi {min_roi}",
    }
