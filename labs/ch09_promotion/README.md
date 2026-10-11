# Lab 09 — Promotion (Chapter 9)

## What this lab is
Keep ≠ promote. A sealed keep enters production only with an HMAC-signed promotion token, a fresh frozen-policy scan whose report hash matches the token, an optional pacing hold for medium/high/critical tiers, and a content-addressed evidence pack for human review.

## Prerequisites
- Python 3.11+
- `pip install -e ".[dev]"`
- Chapter 8 sealed ledger types (`labs.ch08_measure`)
- Optional: `GRSI_PROMOTION_HMAC_KEY` (base64, ≥32 bytes); lab uses a documented ephemeral key when unset

## Repository layout
```
labs/ch09_promotion/
  promotion_gateway.py   # promote() fail-closed gateway
  promotion_records.py   # PromotionRecordStore (required on promote success)
  frozen_policy.py       # Last Frozen Layer scan + report_hash
  risk_tier_token.py     # tier TTL clamps + mint helper
  pacing_hold.py         # void/hold for unverifiable volume
  evidence_pack.py       # reviewer pack + pack_hash
  cli.py
  tests/
```
In-chapter snippets map to `promote`, `run_frozen_policy_scan`, `mint_risk_tier_token`, `PacingHold`, and `build_evidence_pack`. Full modules are on GitHub in this package.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch09_promotion/tests`
3. Accept: `python -m labs.ch09_promotion promote --tier low`
4. Refuse: `python -m labs.ch09_promotion refuse-no-token`

## Expected outputs
- Success: `status: promoted` with `token_id`, `entry_hash`, `scan_report_hash`
- Refuse: `PromotionError` for missing/expired/bad signature token, freeze-scan failure, ledger tip mismatch, or pacing hold

## Insights
- Sealed keep alone never opens production.
- Token binds lineage id and freeze-scan report hash; reminting after scan drift fails closed.
- Medium/high/critical tiers require pacing release; low tier still hits a batch cap.
- Evidence pack hash lets reviewers detect tampering before mint.
- Ledger tip must match the sealed decision presented to promote.

## Lessons
- Human signer + risk tier are part of the authorize surface.
- Frozen-policy scan is re-run at promote time, not trusted from the worker.
- Pacing holds are void states, not soft warnings.
- Cryptographic HMAC verification is required; schema alone is insufficient.
- Chapter 10 publication and kill paths consume the promotion result, not raw keeps.

## Skills you will practice
- HMAC token mint/verify via `rsi_core.crypto_tokens`
- Frozen-policy scan design against ownership manifests
- Risk-tier TTL policy
- Evidence pack content addressing
- Fail-closed promotion gateway testing

## Troubleshooting
| Symptom | Reject class |
|---------|--------------|
| `promotion without token` | Missing token |
| `signature invalid` | Tampered or wrong key |
| `token expired` | TTL elapsed |
| `frozen policy scan failed` | Locked path / non-keep |
| `scan report hash mismatch` | Token minted against stale scan |
| `not the ledger tip` | Decision not tip / chain break |
| `pacing hold` | Tier requires release or batch cap |
| `requires record_store` | Promote success needs PromotionRecordStore |

## Link back to the chapter
Re-read Chapter 9 on keep≠promote, freeze scan, and pacing. Chapter 10 consumes promotion status for publication gates and kill/rollback drills.
