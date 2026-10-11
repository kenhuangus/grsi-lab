# Lab 07 — Isolation (Chapter 7)

## What this lab is
Sandbox profile enforcement with a real filesystem jail, widening guards that stop proposers from editing locked profile fields, an isolation runner that materializes only allowlisted paths, adversary path probes, and broker-owned signed isolation receipts. Done means clean and unclean paths are implemented, tested, and runnable from the CLI — with no held-out scoring inside this package (Chapter 8 owns measure).

## Prerequisites
- Python ≥ 3.11
- From repo root: `pip install -e ".[dev]"`
- Optional: `GRSI_ISOLATION_HMAC_KEY` (defaults to a labeled lab credential)

## Repository layout
```
labs/ch07_isolation/
  sandbox_profile.py   # schema-valid profiles + jail path asserts
  run_isolated.py      # isolation-first runner (no scoring)
  receipts.py          # signed broker-owned receipts
  widening_guard.py    # refuse profile mutation in candidates
  adversary_probes.py  # denied-path fixtures
  __main__.py
  tests/test_ch07.py
```
In-chapter snippets map to `default_lab_profile` / `assert_sandbox_allows` and receipt field minimums; full modules live here on GitHub.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch07_isolation/tests`
3. Happy path: `python -m labs.ch07_isolation run-clean`
4. Refuse paths:
   - `python -m labs.ch07_isolation run-refuse`
   - `python -m labs.ch07_isolation widening-refuse`
   - `python -m labs.ch07_isolation probes`

## Expected outputs
- Clean run returns `ok: true`, `clean: true`, and a signed `receipt_id` stored outside the jail.
- Held-out or evaluator path contact returns unclean receipt; scoring must not proceed.
- Widening proposals raise `WideningViolation` before isolate.
- Adversary probes record clean denies for blocked prefixes.

## Insights
- Receipts must be issued after worker exit, never as provisional “clean” at start.
- A working deny is negative evidence and can remain clean; a slipped allow voids the batch.
- Worker-supplied profiles are refused; runners load locked `profile_id` values only.
- Undeclared egress hosts force `clean: false` even when filesystem asserts passed.
- Tenant ids on receipts prevent cross-tenant score authorization.

## Lessons
- Ownership: sandbox profiles stay in the Last Frozen Layer; proposers cannot vote wider jails.
- Isolate: path asserts, egress, TTL, and budgets are binary gates before measure.
- Measure: Chapter 8 must require a clean `receipt_id` before held-out work.
- Promote: raising budgets or opening egress is human-owned profile versioning (Chapter 9).
- Kill: wall-clock breach marks the receipt unclean and voids scores.

## Skills you will practice
- Schema-valid sandbox profiles with `widening_allowed: false`
- Real filesystem jail binding and allowlist checks
- HMAC-signed isolation receipts and tenant scoping
- Proposal-time widening detection
- Adversary probe fixtures for CI

## Troubleshooting
| Symptom | Likely reject class |
|---------|---------------------|
| `Sandbox blocks evaluator/frozen path` | Diff touched `eval/` / `held_out/` / `ledger/` |
| `Sandbox jail escape` | Absolute path outside logical jail |
| `worker-supplied profiles refused` | Candidate tried to inject profile document |
| `profile_patch touches locked fields` | Widening via egress/TTL/budget patch |
| `tenant mismatch on isolation receipt` | Cross-tenant score attempt |

## Link back to the chapter
Re-read Chapter 7 isolation-first methodology, receipt field list, and widening decision flow if a gate fails. Chapter 8 consumes `receipt_id` / `clean` before adversary pass and sealed keep; do not re-implement the ledger here.
