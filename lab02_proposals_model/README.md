# Lab 02 — Proposals & Model Surface

Planner/implementer proposal engine and a stub LoRA candidate envelope with a forgetting gate. No real GPU or adapter training.

## Modules

- `proposal_engine.py` — build schema-valid candidate diffs by role
- `lora_candidate.py` — stub LoRA envelope + forgetting gate

## Run related tests

```bash
pytest -q tests/test_candidate_diff.py
```
