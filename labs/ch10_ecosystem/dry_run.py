"""Local dry-run of ecosystem controls (no external network)."""

from __future__ import annotations

import uuid
from typing import Any

from labs.ch06_orchestration.harness_store import HarnessStore
from labs.ch08_measure.ledger import SealedLedger
from labs.ch09_promotion.frozen_policy import run_frozen_policy_scan
from labs.ch09_promotion.promotion_gateway import promote
from labs.ch09_promotion.promotion_records import PromotionRecordStore
from labs.ch09_promotion.risk_tier_token import mint_risk_tier_token
from labs.ch10_ecosystem.boundary_proxy import BoundaryProxy, EgressDenied
from labs.ch10_ecosystem.failure_atlas import by_loop_step, load_entries
from labs.ch10_ecosystem.kill_rollback import KillSwitch, kill_and_rollback
from labs.ch10_ecosystem.publication_gate import PublicationError, PublicationGate

MANIFEST: dict[str, Any] = {
    "version": "1.0",
    "components": [
        {
            "path": "adapters/x/",
            "owner": "lab",
            "eval_hook": "eval/score",
            "rollback_unit": "adapters.x",
            "observability_signal": "x_ok",
        }
    ],
    "locked": ["eval/", "held_out/", "ledger/", "CONTRACTS.md"],
}


def run_ecosystem_dry_run() -> dict[str, Any]:
    """Exercise boundary deny, atlas lookup, publication refuse/accept, kill/rollback."""
    steps: list[dict[str, Any]] = []
    lineage = str(uuid.uuid4())
    profile = {
        "profile_id": "lab-eco-profile",
        "filesystem_jail": True,
        "egress_allow": ["example.com"],
        "blocked_paths": ["eval/", "held_out/"],
        "widening_allowed": False,
    }
    proxy = BoundaryProxy(sandbox_profile=profile, allowed_hosts={"example.com"})
    denied = False
    try:
        proxy.request("evil.example", lineage_id=lineage, purpose="exfil")
    except EgressDenied:
        denied = True
    steps.append({"step": "egress_denied", "ok": denied})

    allowed = proxy.request("example.com", lineage_id=lineage, purpose="partner-check")
    steps.append({"step": "egress_allowed", "ok": allowed["status"] == "allowed"})

    channel = proxy.open_delegation_channel(
        channel_id="ch-1",
        delegator_lineage_id=lineage,
        specialist_role="retriever",
        evaluation_gates=["sealed_ledger", "metric_card"],
    )
    steps.append({"step": "delegation_channel", "ok": channel["bypass_sandbox"] is False})

    entries = load_entries()
    promote_failures = by_loop_step(entries, "promote")
    steps.append({"step": "failure_atlas", "ok": len(promote_failures) >= 1})

    gate = PublicationGate(partner_allowlist={"partner-a"})
    empty_store = PromotionRecordStore()
    refused = False
    try:
        gate.publish(
            artifact_id="art-1",
            partner="partner-a",
            promotion_result=None,
            lineage_id=lineage,
            record_store=empty_store,
        )
    except PublicationError:
        refused = True
    steps.append({"step": "publish_without_promote", "ok": refused})

    forged_refused = False
    try:
        gate.publish(
            artifact_id="art-1",
            partner="partner-a",
            promotion_result={
                "status": "promoted",
                "lineage_id": lineage,
                "token_id": "tok-1",
                "entry_hash": "a" * 64,
            },
            lineage_id=lineage,
            record_store=empty_store,
        )
    except PublicationError:
        forged_refused = True
    steps.append({"step": "publish_forged_promote", "ok": forged_refused})

    cand = {
        "lineage_id": lineage,
        "surface": "model",
        "hypothesis": "Improve held-out accuracy",
        "metric": "held_out",
        "rollback": {"unit": "adapters.x", "snapshot_ref": "snap://x"},
        "diff": {"paths": ["adapters/x/"], "summary": "adapter"},
        "proposer_role": "implementer",
    }
    ledger = SealedLedger()
    sealed = ledger.seal(
        lineage_id=lineage,
        decision="keep",
        metric_card_id="lab-metric-card",
        repro_script="running_lab/repro.py",
        scores={"held_out": 0.9},
    )
    scan = run_frozen_policy_scan(
        candidate=cand, ownership_manifest=MANIFEST, sealed_decision=sealed
    )
    token = mint_risk_tier_token(
        token_id="tok-dry-1",
        lineage_id=lineage,
        human_signer="lab-operator",
        risk_tier="low",
        scan_report_hash=scan["report_hash"],
        frozen_policy_scan_passed=bool(scan["passed"]),
    )
    record_store = PromotionRecordStore()
    promoted = promote(
        lineage_id=lineage,
        sealed_decision=sealed,
        token=token,
        ownership_manifest=MANIFEST,
        candidate=cand,
        ledger=ledger,
        record_store=record_store,
    )
    published = gate.publish(
        artifact_id="art-1",
        partner="partner-a",
        promotion_result=promoted,
        lineage_id=lineage,
        record_store=record_store,
    )
    steps.append({"step": "publish_with_promote", "ok": published["status"] == "published"})

    harness = HarnessStore(modules={"planner": {"lr": 0.1}})
    harness.mutate("planner", {"lr": 0.9})
    kill = KillSwitch()
    result = kill_and_rollback(kill, harness, reason="dry-run complete")
    steps.append(
        {
            "step": "kill_rollback",
            "ok": result["kill_engaged"] and harness.modules["planner"]["lr"] == 0.1,
        }
    )

    kill_blocks = False
    try:
        gate.publish(
            artifact_id="art-2",
            partner="partner-a",
            promotion_result=promoted,
            lineage_id=lineage,
            record_store=record_store,
            # gate.kill_engaged after kill_and_rollback on separate object — use kill_switch
        )
    except PublicationError:
        pass
    gate2 = PublicationGate(partner_allowlist={"partner-a"}, kill_switch=kill)
    try:
        gate2.publish(
            artifact_id="art-2",
            partner="partner-a",
            promotion_result=promoted,
            lineage_id=lineage,
            record_store=record_store,
        )
    except PublicationError:
        kill_blocks = True
    steps.append({"step": "kill_blocks_publish", "ok": kill_blocks})

    return {"dry_run": True, "all_ok": all(s["ok"] for s in steps), "steps": steps}
