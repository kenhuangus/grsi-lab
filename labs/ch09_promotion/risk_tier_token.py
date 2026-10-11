"""Risk-tier rules for minting and accepting promotion tokens."""

from __future__ import annotations

from typing import Any

from rsi_core.crypto_tokens import load_signing_key, mint_promotion_token

# Maximum TTL (seconds) allowed per risk tier for lab / teaching deployments.
TIER_MAX_TTL: dict[str, int] = {
    "low": 86_400,
    "medium": 14_400,
    "high": 3_600,
    "critical": 900,
}

# Tiers that may promote without an explicit pacing release (still need a token).
TIER_AUTO_PACING_OK: frozenset[str] = frozenset({"low"})


def tier_allows_promote(risk_tier: str, *, pacing_released: bool = False) -> bool:
    """Return whether ``risk_tier`` may proceed given pacing state."""
    tier = str(risk_tier)
    if tier not in TIER_MAX_TTL:
        return False
    if tier in TIER_AUTO_PACING_OK:
        return True
    return bool(pacing_released)


def mint_risk_tier_token(
    *,
    token_id: str,
    lineage_id: str,
    human_signer: str,
    risk_tier: str,
    scan_report_hash: str,
    frozen_policy_scan_passed: bool = True,
    key: bytes | None = None,
    ttl_seconds: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Mint an HMAC promotion token clamped to the tier's max TTL.

    ``frozen_policy_scan_passed`` must mirror the actual scan; failed scans refuse mint.
    """
    if risk_tier not in TIER_MAX_TTL:
        raise ValueError(f"unknown risk_tier: {risk_tier}")
    max_ttl = TIER_MAX_TTL[risk_tier]
    ttl = max_ttl if ttl_seconds is None else min(int(ttl_seconds), max_ttl)
    if ttl < 1:
        raise ValueError("ttl_seconds must be >= 1")
    return mint_promotion_token(
        token_id=token_id,
        lineage_id=lineage_id,
        human_signer=human_signer,
        risk_tier=risk_tier,
        scan_report_hash=scan_report_hash,
        frozen_policy_scan_passed=frozen_policy_scan_passed,
        key=key or load_signing_key(),
        ttl_seconds=ttl,
        notes=notes,
    )
