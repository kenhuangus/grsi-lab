"""Harness mutation with per-module rollback snapshots and content hashes."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

# Candidates must not self-label keep scores via module state.
SELF_SCORE_KEYS = frozenset(
    {"held_out", "metric", "score", "keep_score", "candidate_score"}
)


def module_hash(state: dict[str, Any]) -> str:
    raw = json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def schema_version(schema: dict[str, Any]) -> str:
    raw = json.dumps(schema, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class ModuleSnapshot:
    """Rollback unit for a single harness module."""

    module_id: str
    state: dict[str, Any]
    state_hash: str = ""

    def __post_init__(self) -> None:
        if not self.state_hash:
            self.state_hash = module_hash(self.state)


@dataclass
class HarnessStore:
    """In-memory harness modules keyed by module_id."""

    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    snapshots: dict[str, ModuleSnapshot] = field(default_factory=dict)
    backbone_pin: str = "backbone-lab-default"
    registered_schemas: dict[str, dict[str, Any]] = field(default_factory=dict)
    accepted_schema_version: str | None = None
    require_registered_schema: bool = False

    def register(self, module_id: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
        if module_id in self.modules:
            raise KeyError(f"Module already registered: {module_id}")
        clean = {
            k: v for k, v in dict(state or {}).items() if k not in SELF_SCORE_KEYS
        }
        self.modules[module_id] = clean
        return self.modules[module_id]

    def register_schema(
        self,
        schema: dict[str, Any],
        *,
        version: str | None = None,
    ) -> str:
        """Persist an accepted tool schema version on this harness store."""
        if not isinstance(schema, dict) or "name" not in schema:
            raise ValueError("schema must be an object with name")
        name = str(schema["name"]).strip()
        if not name:
            raise ValueError("schema name must be non-empty")
        ver = version or schema_version(schema)
        self.registered_schemas[name] = dict(schema)
        self.accepted_schema_version = ver
        return ver

    def get_hash(self, module_id: str) -> str:
        if module_id not in self.modules:
            raise KeyError(f"Unknown module: {module_id}")
        return module_hash(self.modules[module_id])

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
        if self.require_registered_schema and not self.registered_schemas:
            raise ValueError("schema not registered; refuse mutate")
        if not patch:
            raise ValueError("empty patch refused")
        safe_patch = {k: v for k, v in patch.items() if k not in SELF_SCORE_KEYS}
        if not safe_patch:
            raise ValueError("empty patch refused after stripping self-score fields")
        self.snapshot(module_id)
        self.modules[module_id].update(safe_patch)
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

    def policy_token_count(self, module_id: str) -> int:
        """Approximate prompt/policy token pressure from string fields."""
        state = self.modules.get(module_id)
        if state is None:
            raise KeyError(f"Unknown module: {module_id}")
        total = 0
        for value in state.values():
            if isinstance(value, str):
                total += max(1, len(value.split()))
        return total
