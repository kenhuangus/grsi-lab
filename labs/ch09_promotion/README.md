# Chapter 9 — Promotion (`labs/ch09_promotion`)

## What this lab is

Keep ≠ promote. A sealed keep enters production only with an HMAC-signed promotion token, a fresh frozen-policy scan whose report hash matches the token, optional pacing for medium/high/critical tiers, and a content-addressed evidence pack.

## Prerequisites

- Python 3.11+
- `pip install -e ".[dev]"`
- Chapter 8 sealed ledger types (`labs.ch08_measure`)
- Optional: `GRSI_PROMOTION_HMAC_KEY` (base64, ≥32 bytes); lab uses a documented ephemeral key when unset

## How to run

```bash
pytest -q labs/ch09_promotion/tests
python -m labs.ch09_promotion --help
python -m labs.ch09_promotion promote --tier low
python -m labs.ch09_promotion refuse-no-token
```

## Skills learned / insights

- Sealed keep alone never opens production; token binds lineage and freeze-scan report hash.
- Medium/high/critical tiers require pacing release; HMAC verify is required.
- Chapter 10 publication and kill paths consume the promotion result.

## Source

Full code is this directory on GitHub: `labs/ch09_promotion/`.
