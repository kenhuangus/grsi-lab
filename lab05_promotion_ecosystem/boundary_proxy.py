"""Boundary / egress proxy — delegated calls inherit isolation gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rsi_core.schemas_load import validate_instance


class EgressDenied(PermissionError):
    """Raised when egress target is not on the allowlist."""


@dataclass
class BoundaryProxy:
    """Stub egress broker that cannot bypass sandbox or sealed ledger."""

    sandbox_profile: dict[str, Any]
    allowed_hosts: set[str] = field(default_factory=set)
    log: list[dict[str, Any]] = field(default_factory=list)

    def request(
        self,
        host: str,
        *,
        lineage_id: str,
        purpose: str,
    ) -> dict[str, Any]:
        """Attempt egress; deny if host not allowlisted in profile + proxy."""
        profile_allow = set(self.sandbox_profile.get("egress_allow") or [])
        if host not in self.allowed_hosts or host not in profile_allow:
            raise EgressDenied(f"egress denied for host: {host}")
        entry = {
            "host": host,
            "lineage_id": lineage_id,
            "purpose": purpose,
            "status": "allowed",
        }
        self.log.append(entry)
        return entry

    def open_delegation_channel(
        self,
        *,
        channel_id: str,
        delegator_lineage_id: str,
        specialist_role: str,
        evaluation_gates: list[str],
    ) -> dict[str, Any]:
        """Open a schema-valid delegation channel that cannot bypass controls."""
        channel = {
            "channel_id": channel_id,
            "delegator_lineage_id": delegator_lineage_id,
            "specialist_role": specialist_role,
            "inherited_sandbox_profile_id": self.sandbox_profile["profile_id"],
            "evaluation_gates": evaluation_gates,
            "bypass_sandbox": False,
            "bypass_sealed_ledger": False,
            "egress_broker_ref": "boundary_proxy",
        }
        return validate_instance("delegation_channel", channel)
