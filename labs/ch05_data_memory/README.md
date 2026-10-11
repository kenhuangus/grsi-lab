# Lab 05 — Data and Memory (Chapter 5)

## What this lab is
Executable gates for data-surface RSI: experience admission with poison/collapse guards, a generator–validator–curator (GVC) pipeline, batch diversity floors, Token ROI for context-score filters, and a broker-only write path from quarantine to the admitted store. Done means accept and refuse paths are implemented, tested, and runnable from the CLI.

## Prerequisites
- Python ≥ 3.11
- From repo root: `pip install -e ".[dev]"`
- No external network; local filesystem backend under a temp or chosen root

## Repository layout
```
labs/ch05_data_memory/
  admit_experience.py   # admission + leak/entropy guards
  gvc_pipeline.py       # generate → validate → diversity → curate
  diversity_floor.py    # n-gram / fingerprint / tag coverage floors
  token_roi_gate.py     # joint success / tokens / latency band
  broker_client.py      # quarantine → admit → append-only store
  __main__.py           # CLI
  tests/test_ch05.py
```
In-chapter snippets map to `admit_experience`, diversity floor checks, and the broker path; full modules live here on GitHub.

## How to run the lab
1. `pip install -e ".[dev]"`
2. `pytest -q labs/ch05_data_memory/tests`
3. Happy path: `python -m labs.ch05_data_memory broker-demo`
4. Refuse path: `python -m labs.ch05_data_memory diversity-refuse` (exit code 0 when refuse fires)
5. Token ROI refuse: `python -m labs.ch05_data_memory token-roi --success 0.9 --tokens 100 --latency 50 --tags eval_leak`

## Expected outputs
- Admit success returns `admitted: true` with `payload_sha256` and entropy.
- Refuse paths return structured reasons (`blocked tags`, `leak pattern`, `entropy below collapse floor`, diversity / Token ROI failures) and never append to the admitted store.
- GVC discards an entire batch when the diversity floor fails even if per-record quality is high.

## Insights
- Per-record validator scores cannot override a batch diversity floor.
- Collectors must never import the store API; only the broker calls `admit_experience`.
- `eval_leak` / `exfil` tags and payload leak patterns are security refusals, not quality tuning.
- Low Shannon entropy catches degenerate collapse loops before hashing.
- Token ROI fails closed when adversary-tagged notes reach context, regardless of token savings.

## Lessons
- Ownership: blocked-tag sets and collapse floors stay locked unless human promotion changes them.
- Isolate: collection agents remain sandbox candidates (Chapter 7); broker is the only egress to memory.
- Measure: diversity, collapse, and downstream eval (plus Token ROI for filters) bind before keep.
- Promote: admission policy changes that loosen `blocked_tags` are Chapter 9 security work.
- Kill: buffer-full and diversity failures stop collection rather than soft-filling the store.

## Skills you will practice
- Schema-shaped admission policies and fail-closed reason strings
- Append-only corpus roots with content hashes
- Diversity metric design (n-grams, fingerprints, tag coverage)
- Joint accuracy–budget gates for context scoring
- Quarantine / audit / admitted store separation

## Troubleshooting
| Symptom | Likely reject class |
|---------|---------------------|
| `missing lineage_id` | Collector stripped metadata |
| `blocked tags: ['eval_leak']` | Poison / evaluator contamination |
| `entropy below collapse floor` | Degenerate or repeated payload |
| `unique n-gram ratio below floor` | Near-duplicate synthetic batch |
| `adversary tags reached context` | Filter failed hard-reject tags |

## Link back to the chapter
Re-read Chapter 5 sections on the GVC pipeline, experience admission decision tree, and measurement triad if a gate fails. Chapter 6 consumes admitted trajectories via `module_id` for harness ablation; Chapter 7 places the broker behind sandbox profiles.
