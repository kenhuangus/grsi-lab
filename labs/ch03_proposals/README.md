# Chapter 3 — Proposals (`labs/ch03_proposals`)

## What this lab is

Turn improvement ideas into schema-valid `candidate_diff` envelopes before any sandbox run. Planner scopes surface/metric/paths; implementer reuses lineage and emits a concrete diff. Gates refuse untestable, unscoped, and locked-path proposals.

## Prerequisites

- Python 3.11+
- `pip install -e ".[dev]"` from the repository root
- Staging ownership manifest (Chapter 2), e.g. `fixtures/ownership/lab_manifest.json`

## How to run

```bash
pytest -q labs/ch03_proposals/tests
python -m labs.ch03_proposals --help

python -m labs.ch03_proposals plan-implement \
  --manifest fixtures/ownership/lab_manifest.json \
  --hypothesis "Adapter improves held-out accuracy" \
  --metric held_out_accuracy \
  --paths adapters/v1/ \
  --rollback-unit adapters.v1 \
  --snapshot-ref snap://adapters/v1@0 \
  --summary "write adapter_config + weights" \
  --surface model

# Refuse: locked write (exit 1)
python -m labs.ch03_proposals propose \
  --manifest fixtures/ownership/lab_manifest.json \
  --hypothesis "touch eval" --metric m \
  --paths eval/scorer.py --rollback-unit r --snapshot-ref s \
  --summary bad --role implementer
```

## Skills learned / insights

- Build schema-valid envelopes; fail closed on untestable / unscoped / locked_path.
- Shared lineage across planner and implementer; reject rate is the operator signal.
- Ownership reject belongs in the proposal path; keep/revert/reject close lineage (promote is Ch9).

## Source

Full code is this directory on GitHub: `labs/ch03_proposals/`.
