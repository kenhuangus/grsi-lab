# Lab 06 — Orchestration (Chapter 6)

## What this lab is
Harness RSI controls: per-module mutate/rollback (`HarnessStore`), schema/AST gates before hot-reload, a bi-level outer/inner loop with same-model backbone pins, module ablation rows, and a role graph that refuses undeclared collapse. Done means keep and refuse paths are implemented, tested, and runnable from the CLI.

## Prerequisites
- Python ≥ 3.11
- From repo root: `pip install -e ".[dev]"`

## Repository layout
```
labs/ch06_orchestration/
  harness_store.py    # mutate / snapshot / rollback + hashes
  bi_level_loop.py    # propose → schema → score → regress → ablate
  schema_reload.py    # tool JSON + skill AST gates
  ablation.py         # per-module attributable deltas
  role_graph.py       # planner/implementer/verifier wake graph
  __main__.py
  tests/test_ch06.py
```
In-chapter snippets map to `HarnessStore.mutate` / rollback and bi-level gate order; full modules live here on GitHub.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch06_orchestration/tests`
3. Happy path: `python -m labs.ch06_orchestration bi-level --held-out 0.56`
4. Refuse paths:
   - `python -m labs.ch06_orchestration schema-refuse`
   - `python -m labs.ch06_orchestration role-collapse`
   - `python -m labs.ch06_orchestration bi-level --backbone bb-other` (void pin)

## Expected outputs
- Successful bi-level keep reports baseline/candidate scores and ablation clearance (sandbox archive only; promotion is Chapter 9).
- Schema reload raises on writable paths under `eval/` / `held_out/` and on banned skill imports.
- Gains inside the noise floor roll back; backbone pin changes void harness-only claims.
- Undeclared role merges return `ok: false`.

## Insights
- Ablation without a prior snapshot cannot attribute a gain — mutate must snapshot first.
- Same-model backbone pins are measurement integrity, not style.
- In-harness verifier roles never authorize keep; external evaluation stays outside the graph.
- Schema gates must run before isolate so invalid packages never spend sandbox budget.
- Distinct role package hashes detect silent collapse even when cost falls.

## Lessons
- Ownership: tool allowlists and role eval hooks are locked neighbors of mutable prompts.
- Isolate: proposers cannot widen sandbox profiles from skill packages (Chapter 7).
- Measure: regression + noise floor + ablation bind before keep.
- Promote: human Chapter 9 still owns production; bi-level keep is archive-only.
- Kill: `rollback_all` restores every snapshotted module for emergency paths.

## Skills you will practice
- Per-module rollback units and content hashes
- Fail-closed JSON/AST reload gates
- Bi-level loop instrumentation with noise floors
- Ablation matrices for modular keep
- Role-graph wake constraints and collapse detection

## Troubleshooting
| Symptom | Likely reject class |
|---------|---------------------|
| `Unknown module` | Patch targeted unregistered module_id |
| `schema gate refused: locked path` | Tool schema widens into frozen prefixes |
| `gain inside noise floor` | Delta below card noise band |
| `backbone pin changed` | Mixed-surface / weight change mislabeled as harness RSI |
| `undeclared role merge refused` | Role collapse without declared accept |

## Link back to the chapter
Re-read Chapter 6 bi-level loop, RRSI regularization controls, and role-graph sections if a gate fails. Chapter 7 consumes isolation receipts before Chapter 8 scores; pass `module_id` / `profile_id` across the boundary rather than re-implementing sandbox logic here.
