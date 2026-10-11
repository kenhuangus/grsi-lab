"""Adversary probes that exercise sandbox denies before overnight mutate batches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from labs.ch07_isolation.sandbox_profile import (
    SandboxViolation,
    assert_sandbox_allows,
    path_blocked,
)


@dataclass
class ProbeResult:
    name: str
    denied: bool
    clean_deny: bool
    detail: str
    path: str | None = None


@dataclass
class AdversaryProbeReport:
    passed: bool
    reason: str
    probes: list[ProbeResult] = field(default_factory=list)

    @property
    def denied_probes(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "path": p.path,
                "denied": p.denied,
                "clean_deny": p.clean_deny,
                "detail": p.detail,
            }
            for p in self.probes
            if p.denied
        ]


DEFAULT_PROBE_PATHS = (
    ("eval_scorer", "eval/scorer.py"),
    ("held_out_labels", "held_out/private.jsonl"),
    ("ledger_tip", "ledger/tip.json"),
    ("parent_traversal", "work/../../eval/scorer.py"),
    ("absolute_escape", "/etc/passwd"),
)


def run_adversary_probes(
    profile: dict[str, Any],
    *,
    extra_paths: list[tuple[str, str]] | None = None,
    require_all_denied: bool = True,
) -> AdversaryProbeReport:
    """Run path probes; a working deny is recorded and remains clean for the receipt.

    Fail the report when a probe that should be blocked is allowed, or when
    ``require_all_denied`` is set and any default probe slips through.
    """
    probes: list[ProbeResult] = []
    catalog = list(DEFAULT_PROBE_PATHS) + list(extra_paths or [])

    for name, path in catalog:
        try:
            assert_sandbox_allows([path], profile)
            # If we got here, the path was allowed — bad for adversary fixtures
            # unless it is an intentionally allowlisted work path.
            allowed_ok = not path_blocked(path, profile) and path.startswith(
                ("adapters/", "skills/", "work/")
            )
            probes.append(
                ProbeResult(
                    name=name,
                    denied=False,
                    clean_deny=False,
                    detail="probe allowed" if allowed_ok else "probe unexpectedly allowed",
                    path=path,
                )
            )
        except SandboxViolation as exc:
            probes.append(
                ProbeResult(
                    name=name,
                    denied=True,
                    clean_deny=True,
                    detail=str(exc),
                    path=path,
                )
            )

    unexpected_allows = [p for p in probes if not p.denied and "unexpectedly" in p.detail]
    if unexpected_allows:
        return AdversaryProbeReport(
            False,
            f"adversary probe allowed blocked path: {unexpected_allows[0].path}",
            probes,
        )

    denied = [p for p in probes if p.denied]
    if require_all_denied and len(denied) < len(DEFAULT_PROBE_PATHS):
        return AdversaryProbeReport(
            False,
            "not all default adversary probes were denied",
            probes,
        )

    return AdversaryProbeReport(
        True,
        "adversary probes denied as expected",
        probes,
    )
