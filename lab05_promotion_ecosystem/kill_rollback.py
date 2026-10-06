"""Emergency kill switch and rollback helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from lab03_data_orchestration.harness_mutate import HarnessStore


@dataclass
class KillSwitch:
    """Process-local kill flag for RSI loops."""

    engaged: bool = False
    reason: str | None = None
    engaged_at: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def kill(self, reason: str) -> None:
        """Engage the kill switch."""
        self.engaged = True
        self.reason = reason
        self.engaged_at = datetime.now(timezone.utc).isoformat()
        self.events.append(
            {"event": "kill", "reason": reason, "at": self.engaged_at}
        )

    def assert_alive(self) -> None:
        """Raise RuntimeError if the kill switch is engaged."""
        if self.engaged:
            raise RuntimeError(f"kill switch engaged: {self.reason}")


def kill_and_rollback(
    kill_switch: KillSwitch,
    harness: HarnessStore,
    *,
    reason: str,
    on_rollback: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Engage kill switch and roll back all harness module snapshots."""
    kill_switch.kill(reason)
    harness.rollback_all()
    if on_rollback is not None:
        on_rollback()
    return {
        "status": "rolled_back",
        "reason": reason,
        "modules_restored": list(harness.snapshots.keys()),
        "kill_engaged": kill_switch.engaged,
    }
