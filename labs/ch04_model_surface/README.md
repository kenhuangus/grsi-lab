# Chapter 4 — Model surface (`labs/ch04_model_surface`)

## What this lab is

Package model-surface candidates after a Chapter 3 `surface="model"` proposal: on-disk adapter artifacts (config + weight blob, SHA-256), forgetting gate, cheapest-surface escalation, recipe contracts, and pinned train-job records. No GPU training.

## Prerequisites

- Python 3.11+
- `pip install -e ".[dev]"` from the repository root
- A valid Chapter 3 proposal lineage UUID for packaging exercises

## How to run

```bash
pytest -q labs/ch04_model_surface/tests
python -m labs.ch04_model_surface --help

python -m labs.ch04_model_surface package \
  --lineage-id 12345678-1234-4234-8234-123456789abc \
  --adapter-dir /tmp/adapter_v1

python -m labs.ch04_model_surface forget \
  --lineage-id 12345678-1234-4234-8234-123456789abc \
  --adapter-dir /tmp/adapter_v1 \
  --post-scores posts.json

# Refuse: missing post scores (exit 1)
echo {} > posts_empty.json
python -m labs.ch04_model_surface forget \
  --lineage-id 12345678-1234-4234-8234-123456789abc \
  --adapter-dir /tmp/adapter_v1 \
  --post-scores posts_empty.json
```

Other subcommands: `escalate`, `recipe`, `train-job` (see `--help`).

## Skills learned / insights

- Adapter packaging with SHA-256; fail-closed forgetting and tamper detection.
- Escalate to model only with cheaper-surface lineage evidence; recipe drift needs a new lineage.
- Passed forgetting ≠ production ship (Chapter 9).

## Source

Full code is this directory on GitHub: `labs/ch04_model_surface/`.
