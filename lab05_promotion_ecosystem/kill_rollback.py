"""Shim — canonical implementation lives in ``labs.ch10_ecosystem``."""

from labs.ch10_ecosystem.kill_rollback import KillSwitch, kill_and_rollback

__all__ = ["KillSwitch", "kill_and_rollback"]
