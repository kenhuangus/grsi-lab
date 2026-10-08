# Governed Recursive Self-Improvement — Lab Companion

Companion repository for the Packt book **Governed Recursive Self-Improvement**. Labs implement the locked interfaces in [`CONTRACTS.md`](CONTRACTS.md): ownership manifests, candidate diffs, sandboxes, sealed evaluation decisions, and promotion tokens.

**Chapter manuscripts are Google Docs only** — they are not stored in this repo. Doc format matches the Packt template (Crimson Pro / Jost / Consolas); see [`docs/PACKT_FORMAT.md`](docs/PACKT_FORMAT.md). Chapter links: [`docs/GDOC_IDS.json`](docs/GDOC_IDS.json).

RSI loop (lab framing): **propose → isolate → verify/measure → keep/revert → archive → promote → audit**.

## Lab index

| Lab | Package | Focus |
|-----|---------|--------|
| 01 | `lab01_survey_ownership/` | Two-axis taxonomy, keep/revert loop, ownership manifest validation |
| 02 | `lab02_proposals_model/` | Planner/implementer proposals, stub LoRA candidate envelope + forgetting gate |
| 03 | `lab03_data_orchestration/` | Experience admission, harness mutation with per-module rollback |
| 04 | `lab04_isolation_eval/` | Sandbox profiles, adversary checks, sealed ledger hash chain |
| 05 | `lab05_promotion_ecosystem/` | Promotion gateway, boundary proxy, kill/rollback, failure atlas |
| Demo | `running_lab/demo.py` | End-to-end dry-run of the governed loop |

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

## Run the demo (dry-run)

```bash
python -m running_lab.demo --dry-run
# or after install:
grsi-demo
```

The lab run exercises real local gates: propose → filesystem jail → on-disk adapter SHA-256 → metric-card evaluation over fixture datasets → HMAC-signed promotion tokens → kill/rollback. No GPU training is required; adapter artifacts are verified weight blobs plus config.

## Contracts and citations

- Locked schemas: `schemas/*.schema.json` (see `CONTRACTS.md`).
- Packt citation rules for chapter prose: `docs/CITATION_RULES.md`.
- Research briefs and verified facts: `docs/`.

## Note on numbers

This repo does not invent benchmark scores. Use figures only from `docs/VERIFIED_FACTS.md` when writing chapter content.
