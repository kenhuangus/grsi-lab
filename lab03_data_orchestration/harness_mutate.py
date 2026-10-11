"""Shim — canonical implementation lives in ``labs.ch06_orchestration.harness_store``."""

from labs.ch06_orchestration.harness_store import HarnessStore, ModuleSnapshot, module_hash  # noqa: F401

__all__ = ["HarnessStore", "ModuleSnapshot", "module_hash"]
