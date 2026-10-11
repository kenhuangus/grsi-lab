"""Kill switch and harness rollback."""

from __future__ import annotations

import pytest

from labs.ch06_orchestration import HarnessStore
from labs.ch10_ecosystem import KillSwitch, kill_and_rollback


def test_kill_and_rollback_restores_modules() -> None:
    harness = HarnessStore(modules={"planner": {"lr": 0.1}})
    harness.mutate("planner", {"lr": 0.9})
    kill = KillSwitch()
    result = kill_and_rollback(kill, harness, reason="test")
    assert result["status"] == "rolled_back"
    assert kill.engaged is True
    assert harness.modules["planner"]["lr"] == 0.1
    with pytest.raises(RuntimeError, match="kill switch engaged"):
        kill.assert_alive()
