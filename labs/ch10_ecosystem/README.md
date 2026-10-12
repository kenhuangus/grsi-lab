# Chapter 10 — Ecosystem (`labs/ch10_ecosystem`)

## What this lab is

Partner-facing controls: allowlisted egress broker, delegation channels that cannot bypass sandbox/ledger, failure atlas indexing, publication gate (promote required), and kill/rollback. Dry-run exercises refuse and accept paths without external network.

## Prerequisites

- Python 3.11+
- `pip install -e ".[dev]"`
- Seed atlas at `docs/failure_atlas/seed_entries.json`
- No cloud credentials; `BoundaryProxy.enable_network` defaults to False

## How to run

```bash
pytest -q labs/ch10_ecosystem/tests
python -m labs.ch10_ecosystem --help
python -m labs.ch10_ecosystem dry-run
python -m labs.ch10_ecosystem atlas --step promote
```

Dry-run includes publish-without-promote and egress deny among its checks.

## Skills learned / insights

- Egress needs proxy + sandbox allowlists; delegation cannot bypass evaluation gates.
- Publication without a Chapter 9 promote (and store lookup) is void.
- Kill engages before rollback; atlas indexes failures by RSI loop step.

## Source

Full code is this directory on GitHub: `labs/ch10_ecosystem/`.
