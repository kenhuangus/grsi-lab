# Chapter 6 — Orchestration (`labs/ch06_orchestration`)

## What this lab is

Harness RSI controls: per-module mutate/rollback (`HarnessStore`), schema/AST gates before hot-reload, bi-level outer/inner loop with backbone pins, module ablation rows, and a role graph that refuses undeclared collapse.

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`

## How to run

```bash
pytest -q labs/ch06_orchestration/tests
python -m labs.ch06_orchestration --help
python -m labs.ch06_orchestration bi-level --score 0.56
python -m labs.ch06_orchestration schema-refuse
python -m labs.ch06_orchestration role-collapse
python -m labs.ch06_orchestration bi-level --backbone bb-other
```

Also: `mutate-demo` (see `--help`). Bi-level keep is sandbox archive only; promotion is Chapter 9.

## Skills learned / insights

- Snapshot before ablation; same-model backbone pins protect measurement integrity.
- Schema gates run before isolate; undeclared role merges return `ok: false`.
- Bi-level keep ≠ promote.

## Source

Full code is this directory on GitHub: `labs/ch06_orchestration/`.
