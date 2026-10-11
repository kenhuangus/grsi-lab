"""Bi-level harness loop: outer proposer → schema gate → mutate → score → regression."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from labs.ch06_orchestration.ablation import AblationReport, run_module_ablation
from labs.ch06_orchestration.harness_store import SELF_SCORE_KEYS, HarnessStore
from labs.ch06_orchestration.schema_reload import SchemaReloadError, reload_tool_schema

ScoreFn = Callable[[HarnessStore], float]


@dataclass
class BiLevelResult:
    kept: bool
    reason: str
    baseline_score: float | None = None
    candidate_score: float | None = None
    module_id: str | None = None
    ablation: AblationReport | None = None
    details: dict[str, Any] = field(default_factory=dict)


def strip_self_score_fields(patch: Mapping[str, Any]) -> dict[str, Any]:
    """Remove held_out/metric/score keys so candidates cannot set their keep score."""
    return {k: v for k, v in patch.items() if k not in SELF_SCORE_KEYS}


def make_fixture_scorer(
    fixtures: Mapping[str, float],
    *,
    module_id: str = "planner",
    key_field: str = "prompt",
    default: float = 0.0,
) -> ScoreFn:
    """Score from an external fixture map keyed by module field content.

    Never reads ``held_out`` / ``metric`` / ``score`` from module state.
    """

    def score_fn(store: HarnessStore) -> float:
        state = store.modules.get(module_id, {})
        key = str(state.get(key_field, ""))
        return float(fixtures.get(key, default))

    return score_fn


@dataclass
class BiLevelLoop:
    """Outer improver / inner task agent separation with same-model pin."""

    store: HarnessStore
    score_fn: ScoreFn
    noise_floor: float = 0.01
    require_ablation: bool = True
    max_policy_tokens: int | None = None

    def propose_and_evaluate(
        self,
        module_id: str,
        patch: dict[str, Any],
        *,
        tool_schema: dict[str, Any] | None = None,
        skill_source: str | None = None,
        backbone_pin: str | None = None,
    ) -> BiLevelResult:
        """Run schema gate, mutate one module, score, regress, optionally ablate."""
        if backbone_pin is not None and backbone_pin != self.store.backbone_pin:
            return BiLevelResult(
                False,
                "backbone pin changed; void harness-only claim",
                module_id=module_id,
                details={
                    "expected_pin": self.store.backbone_pin,
                    "observed_pin": backbone_pin,
                },
            )

        if tool_schema is not None or skill_source is not None:
            try:
                reload_tool_schema(
                    tool_schema or {"name": "noop", "parameters": {}},
                    skill_source=skill_source,
                    store=self.store,
                )
            except SchemaReloadError as exc:
                return BiLevelResult(False, f"schema gate refused: {exc}", module_id=module_id)

        if self.store.require_registered_schema and not self.store.registered_schemas:
            return BiLevelResult(
                False,
                "schema not registered; refuse mutate",
                module_id=module_id,
            )

        if module_id not in self.store.modules:
            return BiLevelResult(False, f"unknown module: {module_id}", module_id=module_id)

        safe_patch = strip_self_score_fields(patch)
        if not safe_patch:
            return BiLevelResult(
                False,
                "patch empty after stripping self-score fields",
                module_id=module_id,
                details={"stripped_keys": sorted(set(patch) & SELF_SCORE_KEYS)},
            )

        baseline = float(self.score_fn(self.store))
        try:
            self.store.mutate(module_id, safe_patch)
        except (KeyError, ValueError) as exc:
            return BiLevelResult(
                False,
                f"mutate refused: {exc}",
                baseline_score=baseline,
                module_id=module_id,
            )

        if self.max_policy_tokens is not None:
            tokens = self.store.policy_token_count(module_id)
            if tokens > self.max_policy_tokens:
                self.store.rollback(module_id)
                return BiLevelResult(
                    False,
                    "RRSI token ceiling exceeded; rolled back",
                    baseline_score=baseline,
                    module_id=module_id,
                    details={
                        "policy_tokens": tokens,
                        "max_policy_tokens": self.max_policy_tokens,
                    },
                )

        candidate = float(self.score_fn(self.store))
        delta = candidate - baseline

        if delta < -self.noise_floor:
            self.store.rollback(module_id)
            return BiLevelResult(
                False,
                "regression below baseline; rolled back",
                baseline_score=baseline,
                candidate_score=candidate,
                module_id=module_id,
            )

        if abs(delta) < self.noise_floor:
            self.store.rollback(module_id)
            return BiLevelResult(
                False,
                "gain inside noise floor; refused",
                baseline_score=baseline,
                candidate_score=candidate,
                module_id=module_id,
            )

        ablation = None
        if self.require_ablation:
            ablation = run_module_ablation(
                self.store,
                [module_id],
                self.score_fn,
                min_attributable_delta=self.noise_floor,
            )
            if not ablation.passed:
                self.store.rollback(module_id)
                return BiLevelResult(
                    False,
                    ablation.reason,
                    baseline_score=baseline,
                    candidate_score=candidate,
                    module_id=module_id,
                    ablation=ablation,
                )

        return BiLevelResult(
            True,
            "bi-level keep (sandbox archive; promotion is Chapter 9)",
            baseline_score=baseline,
            candidate_score=candidate,
            module_id=module_id,
            ablation=ablation,
            details={"delta": delta, "module_hash": self.store.get_hash(module_id)},
        )
