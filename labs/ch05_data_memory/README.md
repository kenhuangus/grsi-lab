# Chapter 5 — Data and memory (`labs/ch05_data_memory`)

## What this lab is

Data-surface RSI gates: experience admission with poison/collapse guards, GVC pipeline, batch diversity floors, Token ROI for context filters, and broker-only write from quarantine to the admitted store.

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`
- No external network; local filesystem backend under a temp or chosen root

## How to run

```bash
pytest -q labs/ch05_data_memory/tests
python -m labs.ch05_data_memory --help
python -m labs.ch05_data_memory broker-demo
python -m labs.ch05_data_memory diversity-refuse
python -m labs.ch05_data_memory token-roi --success 0.9 --tokens 100 --latency 50 --tags eval_leak
```

Also: `admit`, `gvc-demo` (see `--help`).

## Skills learned / insights

- Batch diversity floors override per-record quality; collectors never import the store API.
- Blocked tags / leak patterns / low entropy are security refusals, not quality tuning.
- Token ROI fails closed when adversary-tagged notes reach context.

## Source

Full code is this directory on GitHub: `labs/ch05_data_memory/`.
