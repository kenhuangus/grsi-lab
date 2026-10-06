"""Harness mutation with per-module rollback snapshots."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModuleSnapshot:
    """Rollback unit for a single harness module."""

    module_id: str
    state: dict[str, Any]


@dataclass
class HarnessStore:
    """In-memory harness modules keyed by module_id."""

    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    snapshots: dict[str, ModuleSnapshot] = field(default_factory=dict)

    def snapshot(self, module_id: str) -> ModuleSnapshot:
        if module_id not in self.modules:
            raise KeyError(f"Unknown module: {module_id}")
        snap = ModuleSnapshot(
            module_id=module_id,
            state=deepcopy(self.modules[module_id]),
        )
        self.snapshots[module_id] = snap
        return snap

    def mutate(self, module_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        """Apply ``patch`` to a module after taking a per-module snapshot."""
        if module_id not in self.modules:
            raise KeyError(f"Unknown module: {module_id}")
        self.snapshot(module_id)
        self.modules[module_id].update(patch)
        return self.modules[module_id]

    def rollback(self, module_id: str) -> dict[str, Any]:
        """Restore a single module from its last snapshot."""
        snap = self.snapshots.get(module_id)
        if snap is None:
            raise KeyError(f"No snapshot for module: {module_id}")
        self.modules[module_id] = deepcopy(snap.state)
        return self.modules[module_id]

    def rollback_all(self) -> None:
        """Restore every module that has a snapshot."""
        for module_id in list(self.snapshots):
            self.rollback(module_id)
