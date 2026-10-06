# Failure Atlas schema

Entries catalog governance / RSI-loop failures keyed by loop step. Used by
`lab05_promotion_ecosystem.failure_atlas` and chapter narrative cross-links.

## Loop steps

| `loop_step` | Meaning |
|-------------|---------|
| `propose` | Untestable / unscoped / locked-path candidate |
| `isolate` | Sandbox escape, egress misuse, profile widening |
| `verify_measure` | Eval gaming, proxy scores without strength, adversary fail |
| `keep_revert` | Incorrect keep/revert under held-out |
| `archive` | Missing lineage close or repro pointer |
| `promote` | Promote without token / frozen-policy fail |
| `audit` | Ledger break, missing sealed decision |

## Entry fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Stable atlas id |
| `loop_step` | string | yes | One of the loop steps above |
| `title` | string | yes | Short failure name |
| `summary` | string | yes | What went wrong |
| `mitigation` | string | yes | Contract / control that blocks it |
| `related_contract` | string | no | Schema or CONTRACTS.md section |
| `refs` | string[] | no | Brief ids only; numbers via VERIFIED_FACTS |

Seed data: [`seed_entries.json`](seed_entries.json).
