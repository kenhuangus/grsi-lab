"""Adapter package artifacts with on-disk SHA-256 verification (Chapter 4)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rsi_core.types import parse_lineage_id


@dataclass
class AdapterPackage:
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

    def __post_init__(self) -> None:
        self.lineage_id = parse_lineage_id(self.lineage_id)

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


# Back-compat alias used by older chapter text / demos.
LoRAEnvelope = AdapterPackage


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
    if not cfg.get("lineage_id"):
        raise ValueError("adapter_config.lineage_id required")
    lineage_id = parse_lineage_id(str(cfg["lineage_id"]))
    return {
        "config_sha256": _sha256_file(config),
        "weights_sha256": _sha256_file(weights),
        "base_model_ref": str(cfg["base_model_ref"]),
        "rank": str(cfg["rank"]),
        "adapter_name": str(cfg.get("adapter_name", root.name)),
        "lineage_id": lineage_id,
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
    if rank < 1:
        raise ValueError("rank must be >= 1")
    if not base_model_ref.strip():
        raise ValueError("base_model_ref required")
    lineage_id = parse_lineage_id(lineage_id)
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


def load_adapter_package(
    lineage_id: str,
    adapter_dir: str | Path,
    *,
    prior_task_scores: dict[str, float],
    forgetting_gate_threshold: float = 0.05,
) -> AdapterPackage:
    """Load and verify an on-disk adapter into an AdapterPackage."""
    lineage_id = parse_lineage_id(lineage_id)
    meta = verify_adapter_artifact(adapter_dir)
    if meta["lineage_id"] != lineage_id:
        raise ValueError(
            f"adapter lineage mismatch: config={meta['lineage_id']} expected={lineage_id}"
        )
    return AdapterPackage(
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


def make_adapter_candidate(
    lineage_id: str,
    adapter_dir: str | Path,
    *,
    base_model_ref: str = "hf://example/base-model",
    adapter_name: str = "candidate-adapter",
    rank: int = 8,
    prior_task_scores: dict[str, float] | None = None,
    forgetting_gate_threshold: float = 0.05,
) -> AdapterPackage:
    """Create verified adapter files and return an AdapterPackage."""
    write_adapter_artifact(
        adapter_dir,
        lineage_id=lineage_id,
        base_model_ref=base_model_ref,
        adapter_name=adapter_name,
        rank=rank,
    )
    return load_adapter_package(
        lineage_id,
        adapter_dir,
        prior_task_scores=prior_task_scores or {"task_a": 0.80, "task_b": 0.75},
        forgetting_gate_threshold=forgetting_gate_threshold,
    )


# Older name retained as alias.
load_lora_envelope = load_adapter_package
