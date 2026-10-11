# Lab 04 — Isolation & Evaluation (legacy package name)

Canonical sandbox / isolation implementation moved to `labs/ch07_isolation/`.
Evaluation / sealed ledger lives in `labs/ch08_measure/` (and remaining `eval_service.py` / `metric_eval.py` shims or modules in this folder for demos).

`sandbox.py` here is a thin re-export of `labs.ch07_isolation.sandbox_profile`.

## Run

```bash
pytest -q labs/ch07_isolation/tests tests/test_sandbox.py
python -m labs.ch07_isolation run-clean
```
