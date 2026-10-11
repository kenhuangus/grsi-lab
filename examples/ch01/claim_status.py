"""Claim-status labels for survey evidence rows (Chapter 1 teaching helper)."""
from __future__ import annotations

from enum import StrEnum


class ClaimStatus(StrEnum):
    PEER_REVIEWED = "peer_reviewed"
    PREPRINT = "preprint"
    LAB_ACCOUNT = "lab_account"
    UNVERIFIED = "unverified"

def may_enter_gate(status: ClaimStatus) -> bool:
    """Only peer-reviewed rows may become numeric gate thresholds."""
    return status is ClaimStatus.PEER_REVIEWED
