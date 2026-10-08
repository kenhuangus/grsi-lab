"""End-to-end lab run smoke (real gates, local artifacts)."""

from __future__ import annotations

from running_lab.demo import main, run_lab


def test_lab_run_all_ok(tmp_path) -> None:
    summary = run_lab(verbose=False, work_dir=tmp_path / "run")
    assert summary["all_ok"] is True
    assert summary["lab_run"] is True


def test_main_lab_exit_zero() -> None:
    assert main(["--lab", "--quiet"]) == 0
