"""Isolation runner: widening guard → path assert → probes → receipt (no scoring)."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from labs.ch07_isolation.adversary_probes import AdversaryProbeReport, run_adversary_probes
from labs.ch07_isolation.receipts import IsolationReceipt, ReceiptStore, issue_receipt
from labs.ch07_isolation.sandbox_profile import (
    SandboxViolation,
    assert_sandbox_allows,
    create_filesystem_jail,
    default_lab_profile,
    load_profile,
    materialize_candidate_paths,
)
from labs.ch07_isolation.widening_guard import WideningViolation, assert_no_widening


def _measured_rss_mb() -> float:
    """Best-effort resident-set sample; never trusts candidate-declared peaks."""
    try:
        import resource

        usage = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        # Linux reports KB; macOS reports bytes.
        if sys.platform == "darwin":
            return usage / (1024.0 * 1024.0)
        return usage / 1024.0
    except (ImportError, AttributeError, OSError):
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            )
            if ok:
                return float(counters.PeakWorkingSetSize) / (1024.0 * 1024.0)
        except (AttributeError, OSError, ValueError, TypeError):
            pass
    return 0.0


@dataclass
class IsolationRunResult:
    ok: bool
    reason: str
    receipt: IsolationReceipt | None = None
    probe_report: AdversaryProbeReport | None = None
    jail_root: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def run_isolated(
    candidate: dict[str, Any],
    *,
    profile: dict[str, Any] | None = None,
    receipt_store: ReceiptStore | None = None,
    materialize: bool = True,
    run_probes: bool = True,
    worker_supplied_profile: dict[str, Any] | None = None,
) -> IsolationRunResult:
    """Execute the isolation-first checklist without computing held-out scores.

    Refuses worker-supplied profiles. Emits a receipt only after checks complete.
    """
    if worker_supplied_profile is not None:
        return IsolationRunResult(
            False,
            "worker-supplied profiles refused; load locked profile_id only",
        )

    locked = load_profile(profile or default_lab_profile())
    try:
        assert_no_widening(candidate, locked_profile=locked)
    except WideningViolation as exc:
        return IsolationRunResult(False, str(exc))

    paths = [str(p) for p in (candidate.get("paths") or candidate.get("diff_paths") or [])]
    if not paths:
        return IsolationRunResult(False, "candidate missing diff paths")

    lineage_id = str(candidate.get("lineage_id") or "")
    if not lineage_id:
        return IsolationRunResult(False, "candidate missing lineage_id")

    started = time.perf_counter()
    jail = create_filesystem_jail()
    try:
        assert_sandbox_allows(paths, locked, jail_root=jail)
    except SandboxViolation as exc:
        receipt = issue_receipt(
            lineage_id=lineage_id,
            profile=locked,
            diff_paths=paths,
            egress_hosts_contacted=[],
            resource_counters={
                "wall_seconds": time.perf_counter() - started,
                "peak_memory_mb": 0,
            },
            clean=False,
            denied_probes=[{"name": "path_assert", "path": exc.path, "detail": str(exc)}],
        )
        if receipt_store is not None:
            receipt_store.put(receipt)
        return IsolationRunResult(
            False,
            f"sandbox path assert failed: {exc}",
            receipt=receipt,
            jail_root=str(jail),
        )

    probe_report = None
    denied: list[dict[str, Any]] = []
    if run_probes:
        probe_report = run_adversary_probes(locked)
        denied = probe_report.denied_probes
        if not probe_report.passed:
            receipt = issue_receipt(
                lineage_id=lineage_id,
                profile=locked,
                diff_paths=paths,
                resource_counters={"wall_seconds": time.perf_counter() - started},
                clean=False,
                denied_probes=denied,
            )
            if receipt_store is not None:
                receipt_store.put(receipt)
            return IsolationRunResult(
                False,
                probe_report.reason,
                receipt=receipt,
                probe_report=probe_report,
                jail_root=str(jail),
            )

    written: list[Path] = []
    if materialize:
        written = materialize_candidate_paths(paths, jail_root=jail)

    hosts = list(candidate.get("egress_hosts_contacted") or [])
    wall = time.perf_counter() - started
    peak_mb = _measured_rss_mb()
    budget = locked["resource_budget"]
    clean = True
    if wall > float(budget["max_wall_seconds"]):
        clean = False
    if peak_mb > float(budget["memory_mb"]):
        clean = False

    receipt = issue_receipt(
        lineage_id=lineage_id,
        profile=locked,
        diff_paths=paths,
        egress_hosts_contacted=hosts,
        resource_counters={
            "wall_seconds": wall,
            "peak_memory_mb": round(peak_mb, 3),
            "cpu_cores_declared": budget["cpu_cores"],
            "files_materialized": len(written),
        },
        clean=clean,
        denied_probes=denied,
        tenant_id=str(candidate.get("tenant_id") or "lab"),
    )
    if receipt_store is not None:
        receipt_store.put(receipt)

    if not clean:
        return IsolationRunResult(
            False,
            "resource budget breached; receipt unclean",
            receipt=receipt,
            probe_report=probe_report,
            jail_root=str(jail),
        )

    return IsolationRunResult(
        True,
        "isolation clean; scoring may proceed in Chapter 8",
        receipt=receipt,
        probe_report=probe_report,
        jail_root=str(jail),
        details={"materialized": [str(p) for p in written]},
    )
