# Lab 08 — Measure (Chapter 8)

## What this lab is
External evaluation for governed RSI: pre-registered metric cards, adversary checks, Token ROI, and a hash-chained sealed ledger. “Done” means `evaluate_keep` refuses without a clean Chapter 7 isolation receipt, refuses gaming candidates, measures held-out scores from on-disk datasets, and seals keep/revert/reject with a verifiable chain tip.

## Prerequisites
- Python 3.11+
- From repo root: `pip install -e ".[dev]"`
- Fixture datasets under `fixtures/datasets/` and card at `fixtures/metric_cards/lab_metric_card.json`
- No GPU or network required

## Repository layout
```
labs/ch08_measure/
  metric_card.py       # load + evaluate metric cards over JSONL
  adversary_pass.py    # static gaming / locked-path checks
  evaluate_keep.py     # isolation receipt → adversary → measure → seal
  ledger.py            # SealedLedger hash chain
  token_roi.py         # Token ROI compute + authorize gate
  cli.py               # operator CLI
  tests/               # accept + refuse coverage
```
In-chapter code snippets map to: `require_isolation_receipt` / `evaluate_keep` (`evaluate_keep.py`), `adversary_pass` (`adversary_pass.py`), `SealedLedger.seal` (`ledger.py`), `evaluate_metric_card` (`metric_card.py`), `gate_token_roi` (`token_roi.py`). Full source is on GitHub in this package.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch08_measure/tests`
3. Accept path: `python -m labs.ch08_measure evaluate`
4. Refuse path (no receipt): `python -m labs.ch08_measure evaluate --no-receipt` (exits non-zero; sealed decision is `reject`)
5. Refuse path (adversary): `python -m labs.ch08_measure adversary --dirty`

## Expected outputs
- Success: sealed decision with `decision: keep`, finite `scores.held_out` / `token_roi`, and `verify_chain() == True`
- Refuse/void: `decision: reject` with notes naming the failed gate (missing receipt, dirty receipt, adversary finding, ablation, Token ROI)

## Insights
- Isolation receipt is checked before held-out spend; scoring without containment is void.
- Callers cannot inject held-out scores; measurement reads JSONL fixtures.
- Ablation scores that beat the full model are treated as a gaming signal.
- Token ROI is computed last from measured numerator and tokens used.
- Ledger tip hash binds the decision for Chapter 9 promotion evidence.

## Lessons
- Measure ≠ promote: a sealed keep stays in sandbox until a Chapter 9 token.
- External evaluator is the only `score_authority`.
- Fail closed on missing receipt, adversary, ablation, or ROI floor.
- Hash-chain integrity is part of the authorize surface, not an audit afterthought.
- Metric cards are Last Frozen Layer; mid-flight card edits are out of band.

## Skills you will practice
- Schema-valid metric cards and sealed decisions
- Fail-closed gate ordering
- Isolation receipt verification before spend
- Multi-seed aggregation and module ablation checks
- Sealed ledger verify and Token ROI gating

## Troubleshooting
| Symptom | Reject class |
|---------|--------------|
| `missing isolation_receipt` | No Chapter 7 handoff on candidate |
| `isolation_receipt not clean` | Contained run failed or forged receipt |
| `path contacts evaluator surface` | Adversary / locked-path contact |
| `module ablation failed` | Ablation missing or beats held-out |
| `token_roi … below min_roi` | ROI authorize floor |
| `verify_chain` false | Tampered or incomplete ledger |

## Link back to the chapter
Re-read Chapter 8 sections on metric cards, adversary ordering, and sealed keep. Chapter 9 consumes the ledger tip hash, card id, isolation receipt id, and repro script pointer when minting a promotion token.
