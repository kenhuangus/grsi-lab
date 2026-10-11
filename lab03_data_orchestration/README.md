# Lab 03 — Data & Orchestration (legacy package name)

Canonical implementations moved to chapter-aligned packages:

- Experience admission → `labs/ch05_data_memory/`
- Harness mutate / rollback → `labs/ch06_orchestration/`

This folder keeps thin import shims for older demos and docs that still reference `lab03_data_orchestration.*`.

## Run

```bash
pytest -q labs/ch05_data_memory/tests labs/ch06_orchestration/tests
python -m labs.ch05_data_memory broker-demo
python -m labs.ch06_orchestration bi-level
```
