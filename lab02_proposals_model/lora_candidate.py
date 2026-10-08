"""Adapter candidate artifacts with on-disk SHA-256 verification + forgetting gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LoRAEnvelope:
    """Adapter candidate backed by real on-disk files (config + weight blob)."""

    lineage_id: str
    base_model_ref: str
    adapter_name: str
    rank: int
    adapter_dir: str
    config_sha256: str
    weights_sha256: str
    target_modules: list[str] = field(default_factory=list)
    forgetting_gate_threshold: float = 0.05
    prior_task_scores: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "base_model_ref": self.base_model_ref,
            "adapter_name": self.adapter_name,
            "rank": self.rank,
            "adapter_dir": self.adapter_dir,
            "config_sha256": self.config_sha256,
            "weights_sha256": self.weights_sha256,
            "target_modules": list(self.target_modules),
            "forgetting_gate_threshold": self.forgetting_gate_threshold,
            "prior_task_scores": dict(self.prior_task_scores),
            "notes": self.notes,
        }


@dataclass
class ForgettingGateResult:
    """Outcome of the forgetting gate."""

    passed: bool
    regressions: dict[str, float]
    message: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_adapter_artifact(adapter_dir: str | Path) -> dict[str, str]:
    """Verify adapter_config.json + adapter_weights.bin exist and return digests."""
    root = Path(adapter_dir)
    config = root / "adapter_config.json"
    weights = root / "adapter_weights.bin"
    if not config.is_file():
        raise FileNotFoundError(f"missing adapter config: {config}")
    if not weights.is_file():
        raise FileNotFoundError(f"missing adapter weights: {weights}")
    cfg = json.loads(config.read_text(encoding="utf-8"))
    if int(cfg.get("rank", 0)) < 1:
        raise ValueError("adapter_config.rank must be >= 1")
    if not cfg.get("base_model_ref"):
        raise ValueError("adapter_config.base_model_ref required")
    return {
        "config_sha256": _sha256_file(config),
        "weights_sha256": _sha256_file(weights),
        "base_model_ref": str(cfg["base_model_ref"]),
        "rank": str(cfg["rank"]),
        "adapter_name": str(cfg.get("adapter_name", root.name)),
        "target_modules": json.dumps(list(cfg.get("target_modules") or [])),
    }


def write_adapter_artifact(
    adapter_dir: str | Path,
    *,
    lineage_id: str,
    base_model_ref: str,
    adapter_name: str,
    rank: int,
    target_modules: list[str] | None = None,
    weight_bytes: bytes | None = None,
) -> Path:
    """Create a real adapter artifact directory with config + weight blob."""
    root = Path(adapter_dir)
    root.mkdir(parents=True, exist_ok=True)
    config = {
        "lineage_id": lineage_id,
        "base_model_ref": base_model_ref,
        "adapter_name": adapter_name,
        "rank": rank,
        "target_modules": target_modules or ["q_proj", "v_proj"],
    }
    (root / "adapter_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Deterministic non-empty weight blob derived from lineage (not GPU training).
    blob = weight_bytes or hashlib.sha256(
        f"{lineage_id}:{adapter_name}:{rank}".encode()
    ).digest() * 64
    (root / "adapter_weights.bin").write_bytes(blob)
    return root


def load_lora_envelope(
    lineage_id: str,
    adapter_dir: str | Path,
    *,
    prior_task_scores: dict[str, float],
    forgetting_gate_threshold: float = 0.05,
) -> LoRAEnvelope:
    """Load and verify an on-disk adapter into a LoRAEnvelope."""
    meta = verify_adapter_artifact(adapter_dir)
    return LoRAEnvelope(
        lineage_id=lineage_id,
        base_model_ref=meta["base_model_ref"],
        adapter_name=meta["adapter_name"],
        rank=int(meta["rank"]),
        adapter_dir=str(Path(adapter_dir)),
        config_sha256=meta["config_sha256"],
        weights_sha256=meta["weights_sha256"],
        target_modules=json.loads(meta["target_modules"]),
        forgetting_gate_threshold=forgetting_gate_threshold,
        prior_task_scores=dict(prior_task_scores),
        notes="verified on-disk adapter artifact",
    )


def forgetting_gate(
    envelope: LoRAEnvelope,
    post_task_scores: dict[str, float],
) -> ForgettingGateResult:
    """Reject candidate if any prior task regresses beyond the threshold.

    Requires complete post scores for every prior task (fail closed).
    """
    # Re-verify artifact still intact at gate time
    meta = verify_adapter_artifact(envelope.adapter_dir)
    if meta["weights_sha256"] != envelope.weights_sha256:
        return ForgettingGateResult(
            passed=False,
            regressions={},
            message="forgetting gate failed: adapter weights digest mismatch",
        )

    regressions: dict[str, float] = {}
    missing: list[str] = []
    for task, prior in envelope.prior_task_scores.items():
        post = post_task_scores.get(task)
        if post is None:
            missing.append(task)
            continue
        drop = prior - post
        if drop > envelope.forgetting_gate_threshold:
            regressions[task] = drop

    if missing:
        return ForgettingGateResult(
            passed=False,
            regressions=regressions,
            message=(
                "forgetting gate failed: missing post scores for "
                + ", ".join(sorted(missing))
            ),
        )
    if regressions:
        return ForgettingGateResult(
            passed=False,
            regressions=regressions,
            message="forgetting gate failed: prior-task regression",
        )
    return ForgettingGateResult(
        passed=True,
        regressions={},
        message="forgetting gate passed",
    )


# Back-compat alias used by older chapter text — creates a real artifact under path.
def make_adapter_candidate(
    lineage_id: str,
    adapter_dir: str | Path,
    *,
    base_model_ref: str = "hf://example/base-model",
    adapter_name: str = "candidate-adapter",
    rank: int = 8,
    prior_task_scores: dict[str, float] | None = None,
) -> LoRAEnvelope:
    """Create verified adapter files and return a LoRAEnvelope."""
    write_adapter_artifact(
        adapter_dir,
        lineage_id=lineage_id,
        base_model_ref=base_model_ref,
        adapter_name=adapter_name,
        rank=rank,
    )
    return load_lora_envelope(
        lineage_id,
        adapter_dir,
        prior_task_scores=prior_task_scores or {"task_a": 0.80, "task_b": 0.75},
    )
