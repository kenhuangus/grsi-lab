# Lab — Ownership Contracts (Chapter 2)

## What this lab is

Fail-closed ownership for RSI: validate a modularity manifest, reject locked or undeclared writes, run the Last Frozen Layer freeze gate, and grade blast radius before isolate. Done means `pytest` accept + refuse paths pass and the CLI prints a structured reject report.

## Prerequisites

- Python 3.11+
- From repo root: `pip install -e ".[dev]"`

## Repository layout

| Module | Role |
|--------|------|
| `manifest.py` | Modularity field checks + locked overlap |
| `reject_locked_writes.py` | Locked / undeclared / traversal rejects |
| `freeze_gate.py` | Last Frozen Layer freeze checklist |
| `blast_radius.py` | Cross-surface blast assessment |
| `cli.py` / `__main__.py` | Operator entrypoints |
| `tests/test_ch02_ownership.py` | Accept + refuse coverage |

In-chapter code snippets excerpt these files; full source is this package on GitHub.

## How to run the lab

```bash
pytest -q labs/ch02_ownership/tests
python -m labs.ch02_ownership --help
python -m labs.ch02_ownership validate --manifest fixtures/ownership/lab_manifest.json
python -m labs.ch02_ownership reject --manifest fixtures/ownership/lab_manifest.json eval/scorer.py
```

Refuse path: locked write (`reject` above). Accept path: declared harness write via `reject ... harness/skills/planner.py`. Freeze accept needs `--evidence` JSON with real artifact paths (bare `--all-evidence` cannot reach `PASSED`).

## Expected outputs

- Accept: empty reject list / freeze gate `ok`
- Refuse: `locked_path`, `undeclared_path`, or `parent_traversal` with non-zero exit

## Insights

- Unscoped path omission and locked-path collision are different reject classes.
- Freeze gate must run before overnight mutate enablement.
- Blast radius scoring is advisory until promotion; ownership reject is hard.

## Lessons

- Publish `locked` before enabling mutation.
- In-harness verifiers must not write external evaluator fixtures.
- Cross-surface edits need an explicit declaration, not a silent multi-path patch.

## Skills you will practice

- Authoring ownership manifests
- Fail-closed path classification
- Freeze-gate operator checks
- Blast-radius worksheet grading in code

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `path overlaps locked` | Component listed under a locked prefix |
| `undeclared_path` | Diff path missing from `components` |
| Schema errors | Manifest missing required component fields |

## Link back to the chapter

Re-read Chapter 2 ownership / Last Frozen Layer sections if rejects fire. Chapter 3 consumes a frozen manifest at `build_proposal`.
