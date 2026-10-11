"""Pacing hold — void/hold state when unverifiable promote volume exceeds tier policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class PacingHoldError(PermissionError):
    """Raised when promotion is held for pacing."""


@dataclass
class PacingHold:
    """Tracks promote attempts per risk tier inside a batch window.

    Medium/high/critical tiers require an explicit ``release`` before promote
    may proceed. Low tier may proceed until ``max_low_per_window`` is exceeded.
    """

    max_low_per_window: int = 5
    held: dict[str, str] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    releases: set[str] = field(default_factory=set)
    events: list[dict[str, Any]] = field(default_factory=list)

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def record_attempt(self, lineage_id: str, risk_tier: str) -> None:
        """Record a promote attempt; may engage a hold for the lineage."""
        tier = str(risk_tier)
        self.counts[tier] = self.counts.get(tier, 0) + 1
        self.events.append(
            {
                "event": "attempt",
                "lineage_id": lineage_id,
                "risk_tier": tier,
                "at": self._now(),
            }
        )
        if tier == "low" and self.counts[tier] > self.max_low_per_window:
            self.engage(lineage_id, reason=f"low-tier batch cap {self.max_low_per_window}")
        elif tier in {"medium", "high", "critical"} and lineage_id not in self.releases:
            self.engage(lineage_id, reason=f"{tier} tier requires pacing release")

    def engage(self, lineage_id: str, *, reason: str) -> None:
        self.held[lineage_id] = reason
        self.events.append(
            {"event": "hold", "lineage_id": lineage_id, "reason": reason, "at": self._now()}
        )

    def release(self, lineage_id: str) -> None:
        self.releases.add(lineage_id)
        self.held.pop(lineage_id, None)
        self.events.append(
            {"event": "release", "lineage_id": lineage_id, "at": self._now()}
        )

    def assert_not_held(self, lineage_id: str) -> None:
        if lineage_id in self.held:
            raise PacingHoldError(f"pacing hold: {self.held[lineage_id]}")

    def is_held(self, lineage_id: str) -> bool:
        return lineage_id in self.held
