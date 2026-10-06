# Lab 05 — Promotion & Ecosystem

Human-signed promotion tokens, boundary proxy for egress, kill/rollback switches, and failure-atlas indexing.

## Modules

- `promotion_gateway.py` — keep ≠ promote; token required
- `boundary_proxy.py` — egress broker stub inheriting sandbox gates
- `kill_rollback.py` — emergency kill + harness rollback
- `failure_atlas.py` — index failure entries by RSI loop step

## Run related tests

```bash
pytest -q tests/test_promotion.py
```
