# Lab 01 — Survey Ownership

Two-axis taxonomy of RSI targets, a minimal evolutionary keep/revert loop, and ownership-manifest validation against locked paths.

## Modules

- `taxonomy.py` — classify a component on (mutable|locked) × (evaluable|not)
- `keep_revert_loop.py` — minimal propose → score → keep|revert cycle
- `manifest_validator.py` — validate modularity contract fields

## Run related tests

```bash
pytest -q tests/test_locked_path.py
```
