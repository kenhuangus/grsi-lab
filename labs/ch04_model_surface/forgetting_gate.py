"""Prior-task forgetting gate — fail closed on missing scores or regressions."""

from __future__ import annotations

from dataclasses import dataclass

from labs.ch04_model_surface.adapter_package import AdapterPackage, verify_adapter_artifact


@dataclass
class ForgettingGateResult:
    """Outcome of the forgetting gate."""

    passed: bool
    regressions: dict[str, float]
    message: str


def forgetting_gate(
    envelope: AdapterPackage,
    post_task_scores: dict[str, float],
) -> ForgettingGateResult:
    """Reject candidate if any prior task regresses beyond the threshold.

    Requires complete post scores for every prior task (fail closed).
    Re-verifies on-disk weight digest at gate time.
    """
    meta = verify_adapter_artifact(envelope.adapter_dir)
    if meta["weights_sha256"] != envelope.weights_sha256:
        return ForgettingGateResult(
            passed=False,
            regressions={},
            message="forgetting gate failed: adapter weights digest mismatch",
        )
    if meta["config_sha256"] != envelope.config_sha256:
        return ForgettingGateResult(
            passed=False,
            regressions={},
            message="forgetting gate failed: adapter config digest mismatch",
        )

    if not envelope.prior_task_scores:
        return ForgettingGateResult(
            passed=False,
            regressions={},
            message="forgetting gate failed: prior_task_scores empty",
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
