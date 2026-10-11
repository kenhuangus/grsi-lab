"""External evaluate_keep: isolation receipt → adversary → metric card → seal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from labs.ch07_isolation.receipts import ReceiptStore, verify_receipt
from labs.ch08_measure.adversary_pass import adversary_pass
from labs.ch08_measure.ledger import SealedLedger
from labs.ch08_measure.metric_card import EvalBundle, evaluate_metric_card, load_metric_card
from labs.ch08_measure.token_roi import gate_token_roi
from rsi_core.schemas_load import validate_instance


def require_isolation_receipt(
    candidate: dict[str, Any],
    *,
    receipt_store: dict[str, dict[str, Any]] | ReceiptStore | None = None,
) -> tuple[bool, list[str]]:
    """Require a Chapter 7 isolation receipt before any held-out spend.

    HMAC signature verification via ``labs.ch07_isolation.receipts.verify_receipt``
    is mandatory. A forged ``{receipt_id, clean: true}`` without a valid signature
    is refused. When a ``ReceiptStore`` is provided, ``require_clean`` is also used.

    Returns ``(ok, findings)``. Findings are non-empty when the gate refuses.
    """
    findings: list[str] = []
    receipt = candidate.get("isolation_receipt")
    if receipt is None:
        return False, ["missing isolation_receipt"]

    if not isinstance(receipt, dict):
        return False, ["isolation_receipt must be an object with receipt_id"]

    receipt_id = receipt.get("receipt_id")
    if not receipt_id or not isinstance(receipt_id, str):
        findings.append("isolation_receipt missing receipt_id")

    if not verify_receipt(receipt):
        findings.append("isolation receipt signature invalid")

    clean = receipt.get("clean")
    if clean is not True:
        findings.append("isolation_receipt not clean")

    if receipt.get("lineage_id") and candidate.get("lineage_id"):
        if receipt["lineage_id"] != candidate["lineage_id"]:
            findings.append("isolation receipt lineage_id mismatch")

    if receipt_store is not None and isinstance(receipt_id, str) and receipt_id:
        if isinstance(receipt_store, ReceiptStore):
            try:
                receipt_store.require_clean(
                    receipt_id,
                    tenant_id=str(receipt.get("tenant_id") or candidate.get("tenant_id") or "lab"),
                )
            except FileNotFoundError:
                findings.append(f"isolation receipt not found in store: {receipt_id}")
            except PermissionError as exc:
                findings.append(str(exc))
        else:
            stored = receipt_store.get(receipt_id)
            if stored is None:
                findings.append(f"isolation receipt not found in store: {receipt_id}")
            else:
                if not verify_receipt(stored):
                    findings.append(
                        f"stored isolation receipt signature invalid: {receipt_id}"
                    )
                if stored.get("clean") is not True:
                    findings.append(f"stored isolation receipt not clean: {receipt_id}")
                if stored.get("lineage_id") and candidate.get("lineage_id"):
                    if stored["lineage_id"] != candidate["lineage_id"]:
                        findings.append("isolation receipt lineage_id mismatch")

    return (not findings, findings)


def evaluate_keep(
    candidate: dict[str, Any],
    ledger: SealedLedger,
    *,
    metric_card: dict[str, Any] | None = None,
    metric_card_path: str | Path | None = None,
    dataset_root: str | Path | None = None,
    repro_script: str = "running_lab/repro.py",
    keep_threshold: float = 0.5,
    ablation_module_scores: dict[str, float] | None = None,
    tokens_used: float = 1000.0,
    min_token_roi: float | None = None,
    receipt_store: dict[str, dict[str, Any]] | ReceiptStore | None = None,
    kill_switch: Any | None = None,
) -> dict[str, Any]:
    """Run isolation receipt + adversary + metric-card evaluation, then seal.

    Gate order (fail closed):
    0. Optional kill switch (must be alive)
    1. Isolation receipt required, clean, and HMAC-verified (Chapter 7 handoff)
    2. Adversary pass
    3. Metric-card measurement (callers may not inject held-out scores)
    4. Module ablation (required scores must be supplied — no soft default)
    5. Optional Token ROI floor
    6. Seal keep / revert / reject
    """
    card_id = "lab-metric-card"
    if metric_card is not None:
        card = validate_instance("metric_card", metric_card)
        card_id = card["card_id"]
    elif metric_card_path is not None:
        card = load_metric_card(metric_card_path)
        card_id = card["card_id"]
    else:
        # labs/ch08_measure/<file> → repo root is parents[2]
        repo_root = Path(__file__).resolve().parents[2]
        card = load_metric_card(repo_root / "fixtures" / "metric_cards" / "lab_metric_card.json")
        card_id = card["card_id"]

    if dataset_root is None:
        dataset_root = Path(__file__).resolve().parents[2] / "fixtures" / "datasets"

    if kill_switch is not None:
        try:
            kill_switch.assert_alive()
        except RuntimeError as exc:
            return ledger.seal(
                lineage_id=candidate["lineage_id"],
                decision="reject",
                metric_card_id=card_id,
                repro_script=repro_script,
                scores={"held_out": 0.0, "held_in": 0.0, "token_roi": 0.0},
                notes=str(exc),
            )

    receipt_ok, receipt_findings = require_isolation_receipt(
        candidate, receipt_store=receipt_store
    )
    if not receipt_ok:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores={"held_out": 0.0, "held_in": 0.0, "token_roi": 0.0},
            notes="; ".join(receipt_findings),
        )

    adv = adversary_pass(candidate)
    if not adv.passed:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores={"held_out": 0.0, "held_in": 0.0, "token_roi": 0.0},
            notes="; ".join(adv.findings),
        )

    ablation_required = bool((card.get("module_ablation") or {}).get("required"))
    if ablation_required and not ablation_module_scores:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores={"held_out": 0.0, "held_in": 0.0, "token_roi": 0.0},
            notes="module ablation required but missing",
        )

    bundle: EvalBundle = evaluate_metric_card(
        card,
        dataset_root=dataset_root,
        ablation_module_scores=ablation_module_scores,
        tokens_used=tokens_used,
    )
    if not bundle.ablation_ok:
        return ledger.seal(
            lineage_id=candidate["lineage_id"],
            decision="reject",
            metric_card_id=card_id,
            repro_script=repro_script,
            scores=bundle.scores,
            notes="module ablation failed",
        )

    if min_token_roi is not None:
        roi_gate = gate_token_roi(
            held_out=bundle.scores["held_out"],
            tokens_used=tokens_used,
            min_roi=min_token_roi,
        )
        if not roi_gate["passed"]:
            return ledger.seal(
                lineage_id=candidate["lineage_id"],
                decision="reject",
                metric_card_id=card_id,
                repro_script=repro_script,
                scores=bundle.scores,
                notes=str(roi_gate["reason"]),
            )

    decision = "keep" if bundle.scores["held_out"] >= keep_threshold else "revert"
    receipt = candidate.get("isolation_receipt") or {}
    return ledger.seal(
        lineage_id=candidate["lineage_id"],
        decision=decision,
        metric_card_id=card_id,
        repro_script=repro_script,
        scores=bundle.scores,
        notes=json.dumps(
            {
                "seeds": bundle.details.get("seeds"),
                "aggregate": bundle.details.get("aggregate"),
                "isolation_receipt_id": receipt.get("receipt_id"),
            }
        ),
    )
