# Lab 03 — Planner / Implementer Proposals (Chapter 3)

## What this lab is
This lab turns improvement ideas into schema-valid `candidate_diff` envelopes before any sandbox run. A planner scopes surface, metric, and paths; an implementer reuses the same lineage and emits a concrete diff summary. Pre-execution gates refuse untestable, unscoped, and locked-path proposals. Optional compute-request envelopes refuse unscoped spends. “Done” means accept only scoped, testable, ownership-clean envelopes with shared lineage.

## Prerequisites
- Python 3.11+
- `pip install -e ".[dev]"` from the repository root
- A staging ownership manifest (Chapter 2) with locked Last Frozen Layer paths

## Repository layout
```
labs/ch03_proposals/
  planner.py           # plan_proposal, plan_then_implement
  implementer.py       # implement_proposal (+ scope-expansion refuse)
  reject_gates.py      # build_proposal + untestable/unscoped/locked gates
  lineage.py           # open/close/assert shared lineage
  compute_request.py   # compute_request build + authorize
  cli.py / __main__.py
  tests/test_ch03_proposals.py
```
In-chapter snippets map to `reject_gates.build_proposal`, `planner.plan_then_implement`, and refuse classes in `reject_gates.py`. Full modules are on GitHub under this directory.

## How to run the lab
1. Install: `pip install -e ".[dev]"`
2. `pytest -q labs/ch03_proposals/tests`
3. CLI happy path:
   ```bash
   python -m labs.ch03_proposals plan-implement \
     --manifest path/to/manifest.json \
     --hypothesis "Adapter improves held-out accuracy" \
     --metric held_out_accuracy \
     --paths adapters/v1/ \
     --rollback-unit adapters.v1 \
     --snapshot-ref snap://adapters/v1@0 \
     --summary "write adapter_config + weights" \
     --surface model
   ```
4. CLI refuse path (locked write — exit 1):
   ```bash
   python -m labs.ch03_proposals propose \
     --manifest path/to/manifest.json \
     --hypothesis "touch eval" --metric m \
     --paths eval/scorer.py --rollback-unit r --snapshot-ref s \
     --summary bad --role implementer
   ```

## Expected outputs
- Success: JSON with `ok: true`, shared `lineage_id`, planner + implementer envelopes, schema-valid fields.
- Refuse: `ok: false` with `reject_class` in `{untestable, unscoped}` or a `LockedPathError` message for Last Frozen Layer hits; exit code 1.

## Insights
- Lineage opens before refuse checks so rejected proposals remain auditable.
- Passing `ownership_manifest=None` skips locks — lab CLI sets `require_manifest=True` so that cannot happen in the graded path.
- Implementer path lists that exceed planner-approved scope are unscoped, not “extra creativity.”
- Compute requests without positive budget, stop rule, or target metric fail like unscoped diffs.
- High proposal volume is not progress; reject rate is the operator signal.

## Lessons
- One surface per envelope; multi-surface product changes need multiple lineages.
- Planner/implementer split keeps scope review separable from mutation.
- Ownership reject belongs in the proposal path, not after isolate.
- Keep/revert/reject close lineage; promote is Chapter 9.
- Measurement of spends belongs to Chapter 8; this lab only gates the request.

## Skills you will practice
- Building schema-valid `candidate_diff` envelopes
- Fail-closed untestable / unscoped / locked_path policy
- Shared lineage across planner and implementer roles
- Compute-request validation and budget authorization
- Stable reject-class telemetry for dashboards

## Troubleshooting
| Symptom | Cause |
|---------|--------|
| `Untestable proposal` | Empty hypothesis or metric |
| `Unscoped proposal: diff.paths` | Empty path list or missing rollback fields |
| `Write rejected: path is locked` | Path under Last Frozen Layer |
| `ownership_manifest is required` | CLI/lab path without staging manifest |
| `implementer paths exceed planner scope` | Scope expansion at implement time |
| `spend amount … outside request budget` | Compute authorize over request amount |

## Link back to the chapter
Re-read Chapter 3 on candidate envelopes, planner/implementer roles, and reject classes R1–R6 if emission fails. Chapter 4 packages model-surface artifacts only after a valid `surface="model"` proposal from this lab.
