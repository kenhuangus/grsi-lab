"""Boundary / egress proxy using real allowlisted HTTP checks (urllib)."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from rsi_core.schemas_load import validate_instance


class EgressDenied(PermissionError):
    """Raised when egress target is not on the allowlist or fails safety checks."""


def _host_is_public(hostname: str) -> bool:
    """Reject localhost / link-local / private IPs (SSRF guard)."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise EgressDenied(f"DNS resolution failed for host: {hostname}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return False
    return True


@dataclass
class BoundaryProxy:
    """Egress broker that cannot bypass sandbox or sealed ledger."""

    sandbox_profile: dict[str, Any]
    allowed_hosts: set[str] = field(default_factory=set)
    log: list[dict[str, Any]] = field(default_factory=list)
    timeout_seconds: float = 5.0
    enable_network: bool = False

    def request(
        self,
        host: str,
        *,
        lineage_id: str,
        purpose: str,
        path: str = "/",
        method: str = "HEAD",
    ) -> dict[str, Any]:
        """Attempt egress; deny if host not allowlisted in profile + proxy."""
        host = host.strip().lower().split(":")[0]
        profile_allow = {h.lower() for h in (self.sandbox_profile.get("egress_allow") or [])}
        if host not in {h.lower() for h in self.allowed_hosts} or host not in profile_allow:
            raise EgressDenied(f"egress denied for host: {host}")

        entry: dict[str, Any] = {
            "host": host,
            "lineage_id": lineage_id,
            "purpose": purpose,
            "status": "allowed",
            "method": method,
            "path": path,
        }

        if self.enable_network:
            if not _host_is_public(host):
                raise EgressDenied(f"egress denied for non-public host: {host}")
            url = f"https://{host}{path if path.startswith('/') else '/' + path}"
            parsed = urlparse(url)
            if parsed.scheme != "https":
                raise EgressDenied("only https egress is permitted")
            req = Request(url, method=method.upper())
            try:
                with urlopen(req, timeout=self.timeout_seconds) as resp:  # nosec B310 — host allowlisted + https
                    entry["http_status"] = getattr(resp, "status", None)
            except URLError as exc:
                raise EgressDenied(f"egress request failed: {exc}") from exc

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
        if not evaluation_gates:
            raise EgressDenied("delegation channel requires evaluation_gates")
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
