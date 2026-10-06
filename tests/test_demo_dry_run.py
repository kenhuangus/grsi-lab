"""Smoke test for running_lab.demo --dry-run."""

from __future__ import annotations

from running_lab.demo import main, run_dry_run


def test_demo_dry_run_smoke() -> None:
    summary = run_dry_run(verbose=False)
    assert summary["dry_run"] is True
    assert summary["all_ok"] is True
    step_names = [s["step"] for s in summary["steps"]]
    assert step_names == [
        "propose",
        "forgetting_gate",
        "sandbox",
        "eval",
        "promote_without_token",
        "kill_rollback",
    ]


def test_demo_main_exit_zero() -> None:
    assert main(["--dry-run", "--quiet"]) == 0
