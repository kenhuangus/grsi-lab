# Governed Recursive Self-Improvement — Lab Companion

Companion repository for the Packt book **Governed Recursive Self-Improvement**. Labs implement the locked interfaces in [`CONTRACTS.md`](CONTRACTS.md): ownership manifests, candidate diffs, sandboxes, sealed evaluation decisions, and promotion tokens.

**Chapter manuscripts are Google Docs only** — they are not stored in this repo. Doc format matches the Packt template (Crimson Pro / Jost / Consolas); see [`docs/PACKT_FORMAT.md`](docs/PACKT_FORMAT.md). Chapter links: [`docs/GDOC_IDS.json`](docs/GDOC_IDS.json).

RSI loop (lab framing): **propose → isolate → verify/measure → keep/revert → archive → promote → audit**.

## Lab index

| Chapter | Package | Purpose |
|--------:|---------|---------|
| 2 | `labs/ch02_ownership/` | Ownership manifest + locked-write refusal |
| 3 | `labs/ch03_proposals/` | Planner/implementer proposals + `candidate_diff` |
| 4 | `labs/ch04_model_surface/` | Adapter/recipe/checkpoint contracts + forgetting gate |
| 5 | `labs/ch05_data_memory/` | Experience admission + poison/collapse controls |
| 6 | `labs/ch06_orchestration/` | Harness mutate / RRSI controls / ablation rows |
| 7 | `labs/ch07_isolation/` | Sandbox profile + isolation receipts |
| 8 | `labs/ch08_measure/` | Metric cards, adversary pass, sealed ledger, Token ROI |
| 9 | `labs/ch09_promotion/` | Keep ≠ promote, freeze scan, risk-tier tokens, pacing |
| 10 | `labs/ch10_ecosystem/` | Boundary broker, failure atlas, kill/rollback, publication |
| Demo | `running_lab/demo.py` | End-to-end local run of the governed loop |

Chapter 1 is survey-only (no graded lab). Legacy `lab01_*`…`lab05_*` packages remain as thin import shims where needed; new work uses `labs.chNN_*`.

## Setup

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
# or: pip install -r requirements.txt && pip install -e .
```

Requires Python 3.11+. Licensed under MIT (`LICENSE`).

## Run tests

```bash
pytest -q
```

CI runs the same suite on Python 3.11–3.13 (see `.github/workflows/ci.yml`).

## Run the demo

```bash
python -m running_lab.demo --lab
# or after install:
grsi-demo
```

The lab run exercises real local gates: propose → filesystem jail → on-disk adapter SHA-256 → metric-card evaluation over fixture datasets (requires a clean isolation receipt) → HMAC-signed promotion tokens → kill/rollback. No GPU training is required; adapter artifacts are verified weight blobs plus config.

## Contracts and citations

- Locked schemas: `schemas/*.schema.json` (see `CONTRACTS.md`).
- Packt citation rules for chapter prose: `docs/CITATION_RULES.md`.
- Research briefs and verified facts: `docs/`.

## Note on numbers

This repo does not invent benchmark scores. Use figures only from `docs/VERIFIED_FACTS.md` when writing chapter content.
