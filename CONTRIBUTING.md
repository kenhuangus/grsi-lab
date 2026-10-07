# Contributing to grsi-lab

This repository is the companion lab for the Packt book **Governed Recursive Self-Improvement**.

## Contracts lock

Do not change `CONTRACTS.md` or `schemas/*.schema.json` without an explicit Lead decision. Keep `rsi_core/schemas/` identical to root `schemas/` when you edit a schema.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
python -m running_lab.demo --dry-run
```

## What belongs in git

- Lab packages, `rsi_core/`, `schemas/`, `tests/`, `running_lab/`, docs that readers need
- Not: `manuscript/`, `publish*.log`, local voice/audit scratch scripts, figure caches

## Pull requests

1. Keep changes focused on one lab or contract surface.
2. Add or update tests under `tests/`.
3. Ensure `pytest -q` and the demo dry-run pass.
