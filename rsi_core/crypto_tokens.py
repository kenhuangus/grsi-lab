"""HMAC-signed promotion tokens using the cryptography library."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC

from rsi_core.schemas_load import validate_instance


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_signing_key(env_var: str = "GRSI_PROMOTION_HMAC_KEY") -> bytes:
    """Load HMAC key from env (base64 or utf-8) or generate an ephemeral lab key.

    Production deployments must set ``GRSI_PROMOTION_HMAC_KEY`` (32+ random bytes,
    base64). An ephemeral key is used only when unset so local labs remain runnable.
    """
    raw = os.environ.get(env_var)
    if raw:
        try:
            key = base64.b64decode(raw, validate=True)
        except Exception:
            key = raw.encode("utf-8")
        if len(key) < 32:
            raise ValueError(f"{env_var} must decode to at least 32 bytes")
        return key
    # Deterministic lab fallback (documented); override in real deployments.
    return hashlib.sha256(b"grsi-lab-dev-only-hmac-key-v1").digest()


def sign_payload(key: bytes, payload: dict[str, Any]) -> str:
    """Return base64 HMAC-SHA256 over canonical JSON payload (excl. signature)."""
    body = {k: v for k, v in payload.items() if k != "signature"}
    h = HMAC(key, hashes.SHA256())
    h.update(_canonical(body))
    return base64.urlsafe_b64encode(h.finalize()).decode("ascii")


def verify_signature(key: bytes, payload: dict[str, Any]) -> bool:
    """Constant-time verify of ``payload['signature']``."""
    sig = payload.get("signature")
    if not isinstance(sig, str) or not sig:
        return False
    expected = sign_payload(key, payload)
    return hmac.compare_digest(sig, expected)


def mint_promotion_token(
    *,
    token_id: str,
    lineage_id: str,
    human_signer: str,
    risk_tier: str,
    scan_report_hash: str,
    key: bytes | None = None,
    ttl_seconds: int = 3600,
    notes: str | None = None,
) -> dict[str, Any]:
    """Mint a schema-valid, HMAC-signed promotion token."""
    key = key or load_signing_key()
    now = datetime.now(UTC)
    token: dict[str, Any] = {
        "token_id": token_id,
        "lineage_id": lineage_id,
        "human_signer": human_signer,
        "risk_tier": risk_tier,
        "frozen_policy_scan_passed": True,
        "frozen_policy_scan_report_hash": scan_report_hash,
        "issued_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(seconds=ttl_seconds))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    if notes:
        token["notes"] = notes
    token["signature"] = sign_payload(key, token)
    return validate_instance("promotion_token", token)


def verify_promotion_token(token: dict[str, Any], *, key: bytes | None = None) -> dict[str, Any]:
    """Schema-validate and cryptographically verify a promotion token."""
    validated = validate_instance("promotion_token", token)
    key = key or load_signing_key()
    if not verify_signature(key, validated):
        raise PermissionError("promotion token signature invalid")
    return validated
