# Chapter 7 — Isolation (`labs/ch07_isolation`)

## What this lab is

Sandbox profile enforcement with a filesystem jail, widening guards, an isolation runner that materializes only allowlisted paths, adversary path probes, and broker-owned signed isolation receipts. No held-out scoring here (Chapter 8 owns measure).

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`
- Optional: `GRSI_ISOLATION_HMAC_KEY` (defaults to a labeled lab credential)

## How to run

```bash
pytest -q labs/ch07_isolation/tests
python -m labs.ch07_isolation --help
python -m labs.ch07_isolation run-clean
python -m labs.ch07_isolation run-refuse
python -m labs.ch07_isolation widening-refuse
python -m labs.ch07_isolation probes
```

## Skills learned / insights

- Receipts issue after worker exit; provisional “clean” at start is invalid.
- Worker-supplied profiles are refused; proposers cannot widen locked profile fields.
- Chapter 8 must require a clean `receipt_id` before held-out work.

## Source

Full code is this directory on GitHub: `labs/ch07_isolation/`.
