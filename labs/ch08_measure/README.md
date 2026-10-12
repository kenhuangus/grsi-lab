# Chapter 8 — Measure (`labs/ch08_measure`)

## What this lab is

External evaluation: pre-registered metric cards, adversary checks, Token ROI, and a hash-chained sealed ledger. `evaluate_keep` refuses without a clean Chapter 7 isolation receipt, refuses gaming candidates, measures held-out scores from on-disk datasets, and seals keep/revert/reject.

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`
- Fixtures: `fixtures/datasets/`, `fixtures/metric_cards/lab_metric_card.json`
- No GPU or network required

## How to run

```bash
pytest -q labs/ch08_measure/tests
python -m labs.ch08_measure --help
python -m labs.ch08_measure evaluate
python -m labs.ch08_measure evaluate --no-receipt
python -m labs.ch08_measure adversary --dirty
python -m labs.ch08_measure verify-ledger
```

## Skills learned / insights

- Isolation receipt before held-out spend; callers cannot inject scores.
- Ablation that beats the full model is a gaming signal; Token ROI is computed last.
- Sealed keep ≠ promote; Chapter 9 consumes the ledger tip.

## Source

Full code is this directory on GitHub: `labs/ch08_measure/`.
