"""Broker-owned isolation receipts emitted only after worker exit."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4


def _lab_receipt_key() -> bytes:
    raw = os.environ.get("GRSI_ISOLATION_HMAC_KEY", "grsi-lab-isolation-dev-key")
    return raw.encode("utf-8")


@dataclass
class IsolationReceipt:
    receipt_id: str
    lineage_id: str
    profile_id: str
    profile_hash: str
    diff_paths: list[str]
    egress_hosts_contacted: list[str]
    credential_issued_at: str
    credential_expires_at: str
    resource_counters: dict[str, Any]
    clean: bool
    runner_build_digest: str
    tenant_id: str = "lab"
    denied_probes: list[dict[str, Any]] = field(default_factory=list)
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def profile_document_hash(profile: dict[str, Any]) -> str:
    raw = json.dumps(profile, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sign(payload: dict[str, Any], key: bytes) -> str:
    body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def issue_receipt(
    *,
    lineage_id: str,
    profile: dict[str, Any],
    diff_paths: list[str],
    egress_hosts_contacted: list[str] | None = None,
    resource_counters: dict[str, Any] | None = None,
    clean: bool,
    runner_build_digest: str = "lab-runner@dev",
    tenant_id: str = "lab",
    denied_probes: list[dict[str, Any]] | None = None,
    credential_ttl_seconds: int | None = None,
    key: bytes | None = None,
) -> IsolationReceipt:
    """Build a signed receipt after worker exit (never provisional at start)."""
    signing_key = key or _lab_receipt_key()
    ttl = int(credential_ttl_seconds or profile.get("credential_ttl_seconds") or 600)
    issued = datetime.now(UTC)
    expires = issued + timedelta(seconds=ttl)
    hosts = list(egress_hosts_contacted or [])
    allow = set(profile.get("egress_allow") or [])
    if any(host not in allow for host in hosts):
        clean = False

    receipt = IsolationReceipt(
        receipt_id=str(uuid4()),
        lineage_id=lineage_id,
        profile_id=str(profile["profile_id"]),
        profile_hash=profile_document_hash(profile),
        diff_paths=list(diff_paths),
        egress_hosts_contacted=hosts,
        credential_issued_at=issued.isoformat(),
        credential_expires_at=expires.isoformat(),
        resource_counters=dict(resource_counters or {}),
        clean=clean,
        runner_build_digest=runner_build_digest,
        tenant_id=tenant_id,
        denied_probes=list(denied_probes or []),
    )
    payload = receipt.to_dict()
    payload.pop("signature", None)
    receipt.signature = _sign(payload, signing_key)
    return receipt


def verify_receipt(receipt: IsolationReceipt | dict[str, Any], *, key: bytes | None = None) -> bool:
    """Verify HMAC signature; workers do not hold the broker key in production."""
    signing_key = key or _lab_receipt_key()
    data = receipt.to_dict() if isinstance(receipt, IsolationReceipt) else dict(receipt)
    sig = data.pop("signature", "")
    expected = _sign(data, signing_key)
    return hmac.compare_digest(sig, expected)


class ReceiptStore:
    """Broker-owned store outside the jail (local FS backend for the lab)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._by_id: dict[str, IsolationReceipt] = {}

    def put(self, receipt: IsolationReceipt) -> Path:
        if not verify_receipt(receipt):
            raise ValueError("refusing to store receipt with invalid signature")
        path = self.root / f"{receipt.receipt_id}.json"
        path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
        self._by_id[receipt.receipt_id] = receipt
        return path

    def get(self, receipt_id: str) -> IsolationReceipt | None:
        return self._by_id.get(receipt_id)

    def require_clean(self, receipt_id: str, *, tenant_id: str | None = None) -> IsolationReceipt:
        receipt = self.get(receipt_id)
        if receipt is None:
            raise FileNotFoundError(f"missing isolation receipt: {receipt_id}")
        if tenant_id is not None and receipt.tenant_id != tenant_id:
            raise PermissionError("tenant mismatch on isolation receipt")
        if not receipt.clean:
            raise PermissionError("isolation receipt not clean; scoring void")
        if not verify_receipt(receipt):
            raise PermissionError("isolation receipt signature invalid")
        return receipt
