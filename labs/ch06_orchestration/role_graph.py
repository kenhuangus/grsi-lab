"""Role graph for planner / implementer / in-harness verifier packages."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RoleSpec:
    role_id: str
    package_path: str
    allowed_tools: list[str] = field(default_factory=list)
    max_steps: int = 8
    eval_hook: str = ""
    rollback_unit: str = ""
    instructions: str = ""

    def package_hash(self) -> str:
        material = {
            "role_id": self.role_id,
            "package_path": self.package_path,
            "allowed_tools": self.allowed_tools,
            "max_steps": self.max_steps,
            "eval_hook": self.eval_hook,
            "rollback_unit": self.rollback_unit,
            "instructions": self.instructions,
        }
        raw = json.dumps(material, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass
class RoleGraph:
    """Mutable orchestration surface when each role is independently editable."""

    roles: dict[str, RoleSpec] = field(default_factory=dict)
    wake_edges: dict[str, list[str]] = field(default_factory=dict)
    external_evaluator: str = "external_evaluator"

    def add_role(self, spec: RoleSpec) -> None:
        if not spec.role_id:
            raise ValueError("role_id required")
        if not spec.eval_hook:
            raise ValueError(f"role {spec.role_id} missing eval_hook")
        if not spec.rollback_unit:
            raise ValueError(f"role {spec.role_id} missing rollback_unit")
        if spec.role_id == self.external_evaluator:
            raise ValueError("cannot register external evaluator inside harness graph")
        self.roles[spec.role_id] = spec

    def declare_wake(self, chief_id: str, specialist_ids: list[str]) -> None:
        if chief_id not in self.roles:
            raise KeyError(f"unknown chief role: {chief_id}")
        for sid in specialist_ids:
            if sid not in self.roles:
                raise KeyError(f"unknown specialist role: {sid}")
        self.wake_edges[chief_id] = list(specialist_ids)

    def can_wake(self, chief_id: str, specialist_id: str) -> bool:
        return specialist_id in self.wake_edges.get(chief_id, [])

    def distinct_role_hashes(self) -> set[str]:
        return {spec.package_hash() for spec in self.roles.values()}

    def detect_role_collapse(self, *, prior_hash_count: int | None = None) -> dict[str, Any]:
        """Refuse undeclared collapse when distinct package hashes shrink."""
        current = len(self.distinct_role_hashes())
        expected = prior_hash_count if prior_hash_count is not None else len(self.roles)
        collapsed = current < min(expected, len(self.roles))
        return {
            "collapsed": collapsed,
            "distinct_hashes": current,
            "role_count": len(self.roles),
            "reason": "role collapse detected" if collapsed else "role graph modular",
        }

    def merge_roles(self, into_id: str, from_id: str, *, declared: bool = False) -> dict[str, Any]:
        """Merge specialist instructions into another role; refuse unless declared."""
        if not declared:
            return {
                "ok": False,
                "reason": "undeclared role merge refused",
            }
        if into_id not in self.roles or from_id not in self.roles:
            raise KeyError("merge requires existing roles")
        target = self.roles[into_id]
        source = self.roles[from_id]
        target.instructions = (target.instructions + "\n" + source.instructions).strip()
        target.allowed_tools = sorted(set(target.allowed_tools) | set(source.allowed_tools))
        del self.roles[from_id]
        for chief, specs in list(self.wake_edges.items()):
            self.wake_edges[chief] = [s for s in specs if s != from_id]
        return {"ok": True, "reason": "declared merge applied", "remaining": sorted(self.roles)}
