# Chapter 2 — Ownership (`labs/ch02_ownership`)

## What this lab is

Fail-closed ownership for RSI: validate a modularity manifest, reject locked or undeclared writes, run the Last Frozen Layer freeze gate, and grade blast radius before isolate.

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`

## How to run

```bash
pytest -q labs/ch02_ownership/tests
python -m labs.ch02_ownership --help
python -m labs.ch02_ownership validate --manifest fixtures/ownership/lab_manifest.json
python -m labs.ch02_ownership reject --manifest fixtures/ownership/lab_manifest.json eval/scorer.py
python -m labs.ch02_ownership reject --manifest fixtures/ownership/lab_manifest.json harness/skills/planner.py
```

Refuse: locked write (`eval/scorer.py`). Accept: declared harness path. Freeze accept needs `--evidence` JSON with real artifact paths (bare `--all-evidence` cannot reach `PASSED`).

## Skills learned / insights

- Author ownership manifests; classify locked vs undeclared vs traversal rejects.
- Freeze gate runs before overnight mutate; blast radius is advisory until promotion.
- Publish `locked` before enabling mutation; cross-surface edits need explicit declaration.

## Source

Full code is this directory on GitHub: `labs/ch02_ownership/`.
