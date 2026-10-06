# Lab 04 — Isolation & Evaluation

Sandbox profiles that block evaluator paths, plus an external eval service with an adversary pass and sealed ledger hash chain.

## Modules

- `sandbox.py` — filesystem jail checks; blocked evaluator paths
- `eval_service.py` — adversary checks + sealed decision ledger

## Run related tests

```bash
pytest -q tests/test_sandbox.py tests/test_sealed_ledger.py
```
