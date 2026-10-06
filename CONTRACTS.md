# CONTRACTS.md — LOCKED interfaces for GRSI running lab

> Wave 2 chapter/code agents must **not** change these contracts without Lead approval.
> All implementations live under `rsi_core/` and lab packages that import these schemas.

## Glossary

| Term | Meaning |
|------|---------|
| RSI | Recursive self-improvement: propose → isolate → verify/measure → keep/revert → archive → promote → audit |
| Surface | Stack area a candidate may mutate: `model`, `data`, `orchestration`, `research_process` |
| Last Frozen Layer | Artifacts no RSI cycle may redefine (evaluators, held-out sets, metric cards, ledger, sandbox/egress, promotion policy, safety constitution, ownership manifest) |
| In-harness verifier | Agent role that checks its own work; **may** mutate under ownership contract |
| External evaluator | Authority that scores candidates; **never** mutates inside the loop it grades |
| Lineage ID | UUID opened at proposal time; closed at keep/revert/reject |

## 1. Ownership manifest (Ch 2)

Schema: `schemas/ownership_manifest.schema.json`

- Every mutable component declares: `owner`, `eval_hook`, `rollback_unit`, `observability_signal`
- Writes to paths listed under `locked` **must** raise `LockedPathError`
- Modularity contract: independently editable, evaluable, and roll-backable — or not an RSI target

## 2. Candidate diff envelope (Ch 3)

Schema: `schemas/candidate_diff.schema.json`

Required fields: `lineage_id`, `surface`, `hypothesis`, `metric`, `rollback`, `diff`, `proposer_role`

Reject before execution if: untestable, unscoped, or touches locked paths.

## 3. Compute-request envelope (Ch 3, optional)

Schema: `schemas/compute_request.schema.json`

Required: `budget`, `target_metric`, `stop_rule`, `lineage_id`

Unscoped compute spends are rejected like unscoped diffs. Measurement belongs to Ch 8.

## 4. Sandbox profile (Ch 7)

Schema: `schemas/sandbox_profile.schema.json`

- Allowlists, filesystem jail, egress filters, credential TTLs, resource budgets
- Proposer **cannot** widen its own profile
- Profile itself is Last Frozen Layer unless ownership manifest explicitly allows infra tuning

## 5. Metric card + sealed decision (Ch 8)

Schemas: `schemas/metric_card.schema.json`, `schemas/sealed_decision.schema.json`

- Held-in / held-out, multi-seed, module ablation, Token ROI fields
- Decision ∈ {`keep`, `revert`, `reject`} with hash-chained ledger entry and repro script pointer
- External evaluator is sole score authority

## 6. Promotion token (Ch 9)

Schema: `schemas/promotion_token.schema.json`

- Human-signed; risk tier; frozen-policy scan must pass
- Kept-in-sandbox is **not** production

## 7. Delegation / egress broker (Ch 10)

Schema: `schemas/delegation_channel.schema.json`

- Delegated specialist inherits delegator isolation profile and evaluation gates
- Delegation must not bypass sandbox or sealed ledger

## Surface tags (enum)

`model` | `data` | `orchestration` | `research_process`

Evaluator and environment targets are **surveyed** but not opened for mutation in this lab.
