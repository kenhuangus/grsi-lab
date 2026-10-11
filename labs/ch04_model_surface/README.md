# Lab 04 — Model Surface Packages & Forgetting (Chapter 4)

## What this lab is
This lab packages model-surface candidates after a Chapter 3 `surface="model"` proposal. You write and verify on-disk adapter artifacts (config + weight blob with SHA-256), run a fail-closed forgetting gate, enforce cheapest-surface escalation before opening weights, pin SFT/DPO/RLAIF recipe contracts, and open train-job records only when metric-card and sandbox pins exist. No GPU training is required. “Done” means accept only verified packages that pass forgetting and escalation, and refuse missing scores, regressions, tampering, recipe drift, and unpinned train opens.

## Prerequisites
- Python 3.11+
- `pip install -e ".[dev]"` from the repository root
- A valid Chapter 3 proposal lineage UUID for packaging exercises

## Repository layout
```
labs/ch04_model_surface/
  adapter_package.py    # write/verify AdapterPackage (SHA-256)
  forgetting_gate.py    # prior-task regression gate (fail closed)
  cheapest_surface.py   # escalate to model only with lineage evidence
  recipe_contract.py    # SFT/DPO/RLAIF frozen recipe + drift refuse
  train_job_record.py   # pinned train-job open (no GPU)
  cli.py / __main__.py
  tests/test_ch04_model_surface.py
```
In-chapter snippets map to `adapter_package.AdapterPackage`, `forgetting_gate.forgetting_gate`, and `cheapest_surface.require_cheapest_surface`. Full modules are on GitHub under this directory.

## How to run the lab
1. Install: `pip install -e ".[dev]"`
2. `pytest -q labs/ch04_model_surface/tests`
3. CLI happy path:
   ```bash
   python -m labs.ch04_model_surface package \
     --lineage-id 12345678-1234-4234-8234-123456789abc \
     --adapter-dir /tmp/adapter_v1
   python -m labs.ch04_model_surface forget \
     --lineage-id 12345678-1234-4234-8234-123456789abc \
     --adapter-dir /tmp/adapter_v1 \
     --post-scores posts.json
   ```
4. CLI refuse path (missing post scores — exit 1):
   ```bash
   echo {} > posts_empty.json
   python -m labs.ch04_model_surface forget \
     --lineage-id 12345678-1234-4234-8234-123456789abc \
     --adapter-dir /tmp/adapter_v1 \
     --post-scores posts_empty.json
   ```

## Expected outputs
- Success: `ok: true` with package digests, forgetting `passed`, escalation `allowed`, recipe hash, queued train-job record.
- Refuse: `ok: false` for missing post scores, prior-task regression, digest mismatch, empty cheaper-surface evidence, DPO without judge, recipe drift, or missing metric-card pins.

## Insights
- Missing post scores fail closed; skipping a prior task is not a pass.
- Weight digest is re-checked at forgetting-gate time so tampering voids the candidate.
- “We tried a prompt edit last month” without a lineage UUID is not escalation evidence.
- DPO/RLAIF recipes without `judge_ref` are unscoped, same class as empty paths in Chapter 3.
- Train-job open without metric-card SHA-256 is refused before any sandbox train.

## Lessons
- Model surface carries the highest blast radius; try harness/experience first.
- Adapter accept decisions must stay separable from recipe and checkpoint pins.
- Thresholds belong on the frozen metric card, not in proposer-owned envelope fields in production.
- Silent base-model swaps require a new lineage.
- Keep ≠ promote: a passed forgetting gate is not a production ship (Chapter 9).

## Skills you will practice
- On-disk adapter packaging with SHA-256 verification
- Fail-closed forgetting and tamper detection
- Cheapest-surface escalation with lineage citations
- Recipe contract hashing and drift refusal
- Train-job pin completeness before isolate/train

## Troubleshooting
| Symptom | Cause |
|---------|--------|
| `missing post scores` | Prior task absent from post dict |
| `prior-task regression` | Drop exceeds threshold |
| `digest mismatch` | Weights/config changed after package load |
| `no cheaper-surface lineage evidence` | Escalation checklist incomplete |
| `judge_ref required for dpo` | Preference recipe missing judge pin |
| `recipe drift without new lineage` | Mid-run mix/loss/schedule change |
| `metric card id and sha256 required` | Train job opened without card pin |

## Link back to the chapter
Re-read Chapter 4 on adapter/recipe/checkpoint objects, forgetting gates, and cheapest-surface escalation if a refuse fires. Chapter 5 owns experience admission into training mixes; this lab only verifies the mix id on the recipe card.
