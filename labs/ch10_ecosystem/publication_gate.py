"""Publication gate — refuse partner/public publish without a verified promote token."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rsi_core.crypto_tokens import load_signing_key, verify_promotion_token

if TYPE_CHECKING:
    from labs.ch09_promotion.promotion_records import PromotionRecordStore


class PublicationError(PermissionError):
    """Raised when publication is attempted without a valid promote result."""


@dataclass
class PublicationGate:
    """Fail-closed publisher for partner allowlists and public artifacts."""

    partner_allowlist: set[str] = field(default_factory=set)
    log: list[dict[str, Any]] = field(default_factory=list)
    kill_engaged: bool = False
    kill_switch: Any | None = None

    def publish(
        self,
        *,
        artifact_id: str,
        partner: str,
        promotion_result: dict[str, Any] | None,
        lineage_id: str,
        record_store: PromotionRecordStore | None = None,
        key: bytes | None = None,
    ) -> dict[str, Any]:
        """Publish only when kill is clear, partner allowlisted, and promote verifies.

        Requires a ``PromotionRecordStore`` lookup for the lineage — a forged
        ``{status: "promoted", promotion_record_persisted: true, token: ...}``
        dict without a matching persisted record is refused even when the HMAC
        token verifies under the lab key.
        """
        if self.kill_switch is not None:
            try:
                self.kill_switch.assert_alive()
            except RuntimeError as exc:
                raise PublicationError(f"publication blocked: {exc}") from exc
        if self.kill_engaged:
            raise PublicationError("publication blocked: kill switch engaged")
        if promotion_result is None:
            raise PublicationError("publication without promotion result fails")
        if record_store is None:
            raise PublicationError(
                "publication requires PromotionRecordStore to verify "
                "persisted promotion record"
            )
        if promotion_result.get("status") != "promoted":
            raise PublicationError("publication requires status=promoted")
        if promotion_result.get("lineage_id") != lineage_id:
            raise PublicationError("promotion result lineage_id mismatch")
        if promotion_result.get("promotion_record_persisted") is not True:
            raise PublicationError(
                "publication requires persisted promotion record "
                "(promotion_record_persisted=true)"
            )
        if not promotion_result.get("entry_hash"):
            raise PublicationError("publication requires sealed entry_hash from promote")

        stored = record_store.find_by_lineage(lineage_id)
        if stored is None:
            raise PublicationError(
                f"no persisted promotion record for lineage: {lineage_id}"
            )
        if stored.get("status") != "promoted":
            raise PublicationError("persisted promotion record status is not promoted")
        if stored.get("entry_hash") != promotion_result.get("entry_hash"):
            raise PublicationError(
                "entry_hash mismatch vs persisted promotion record"
            )
        if stored.get("token_id") != promotion_result.get("token_id"):
            raise PublicationError(
                "token_id mismatch vs persisted promotion record"
            )

        token = promotion_result.get("token")
        if not isinstance(token, dict):
            raise PublicationError("publication requires verified promotion token")
        try:
            verified = verify_promotion_token(token, key=key or load_signing_key())
        except Exception as exc:
            raise PublicationError(f"promotion token verification failed: {exc}") from exc
        if verified.get("lineage_id") != lineage_id:
            raise PublicationError("promotion token lineage_id mismatch")
        if verified.get("frozen_policy_scan_passed") is not True:
            raise PublicationError("promotion token frozen_policy_scan_passed is not true")
        if verified.get("token_id") != promotion_result.get("token_id"):
            raise PublicationError("promotion result token_id mismatch")
        if verified.get("token_id") != stored.get("token_id"):
            raise PublicationError(
                "verified token_id mismatch vs persisted promotion record"
            )

        partner_norm = partner.strip().lower()
        if partner_norm not in {p.lower() for p in self.partner_allowlist}:
            raise PublicationError(f"partner not allowlisted: {partner}")

        entry = {
            "status": "published",
            "artifact_id": artifact_id,
            "partner": partner_norm,
            "lineage_id": lineage_id,
            "token_id": verified.get("token_id"),
            "entry_hash": promotion_result.get("entry_hash"),
        }
        self.log.append(entry)
        return entry
