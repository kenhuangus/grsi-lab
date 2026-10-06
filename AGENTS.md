# AGENTS.md — GRSI lab companion

## Packt citation rules

Chapter prose for this title follows [`docs/CITATION_RULES.md`](docs/CITATION_RULES.md):

- No end-of-chapter References/Sources section.
- First citation of a work in a chapter: canonical URL inline once.
- Same URL must not repeat in that chapter; later mentions use prose back-reference.
- Quantitative claims must exist in [`docs/VERIFIED_FACTS.md`](docs/VERIFIED_FACTS.md).

## Contracts lock

[`CONTRACTS.md`](CONTRACTS.md) defines the locked interfaces for this running lab.

- Do **not** change schemas under `schemas/` or the glossary/surface enum without Lead approval.
- Implementations live under `rsi_core/` and lab packages that import those schemas.
- Writes to ownership-manifest `locked` paths must raise `LockedPathError`.

## Lab conventions

- Python 3.11+, type hints, stub ML only (no real GPU/LoRA training).
- Prefer envelopes, gates, and hash-chained ledgers over invented benchmark numbers.
- Run tests with `pip install -e ".[dev]"` then `pytest -q`.
