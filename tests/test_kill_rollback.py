"""Kill switch and harness rollback."""

from __future__ import annotations

import pytest

from lab03_data_orchestration.harness_mutate import HarnessStore
from lab05_promotion_ecosystem.kill_rollback import KillSwitch, kill_and_rollback


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
