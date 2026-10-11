# Lab 10 — Ecosystem (Chapter 10)

## What this lab is
Partner-facing ecosystem controls: allowlisted egress broker, delegation channels that cannot bypass sandbox/ledger, failure atlas indexing, publication gate (promote required), and kill/rollback. The dry-run exercises refuse and accept paths without external network.

## Prerequisites
- Python 3.11+
- `pip install -e ".[dev]"`
- Seed atlas at `docs/failure_atlas/seed_entries.json`
- No cloud credentials; `BoundaryProxy.enable_network` defaults to False

## Repository layout
```
labs/ch10_ecosystem/
  boundary_proxy.py    # egress + delegation channel
  failure_atlas.py     # loop-step indexed failures
  kill_rollback.py     # KillSwitch + rollback harness protocol
  publication_gate.py  # partner publish requires store-backed Ch9 promote
  dry_run.py           # local end-to-end ecosystem drill
  cli.py
  tests/
```
In-chapter snippets map to `BoundaryProxy.request`, `open_delegation_channel`, `PublicationGate.publish`, `kill_and_rollback`, and `by_loop_step`. Full modules are on GitHub in this package.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch10_ecosystem/tests`
3. Accept path: `python -m labs.ch10_ecosystem dry-run`
4. Refuse path: dry-run includes publish-without-promote and egress deny; or call `PublicationGate.publish(..., promotion_result=None)` in a REPL

## Expected outputs
- Success: dry-run `all_ok: true`; publish `status: published`; kill restores module snapshots
- Refuse: `EgressDenied`, `PublicationError`, or kill `RuntimeError` on `assert_alive`

## Insights
- Egress requires both proxy allowlist and sandbox profile allowlist.
- Delegation channels force `bypass_sandbox` / `bypass_sealed_ledger` false.
- Publication without a Chapter 9 promote result (and matching `PromotionRecordStore` lookup) is void.
- Kill engages before rollback so in-flight loops stop.
- Atlas entries are indexed by RSI loop step for operator triage.

## Lessons
- Ecosystem partners inherit evaluation gates; they do not widen them.
- Publish is a separate authorize surface from sealed keep.
- Kill/rollback pairs with harness snapshots (Chapter 6 store).
- Failure atlas is operational memory, not a substitute for sealed ledger.
- Residual risk remains: single-process broker, local FS — controls are complete for the lab threat model.

## Skills you will practice
- Allowlist egress design with SSRF guards
- Schema-valid delegation channels
- Publication fail-closed gates
- Kill switch + harness rollback
- Failure atlas triage by loop step

## Troubleshooting
| Symptom | Reject class |
|---------|--------------|
| `egress denied for host` | Not on proxy+profile allowlist |
| `delegation channel requires evaluation_gates` | Empty gates |
| `publication without promotion result` | Missing Ch9 promote |
| `partner not allowlisted` | Partner policy |
| `kill switch engaged` | Loop halted |
| Unknown loop step | Atlas filter typo |

## Link back to the chapter
Re-read Chapter 10 on broker, atlas, kill, and publication. Earlier chapters supply ownership, isolation receipts, sealed keeps, and promotion tokens this lab consumes.
