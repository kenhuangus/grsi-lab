# GRSI chapter plan (updated) — labs, code blocks, production GitHub

**Status:** Binding editorial + repo plan (supersedes paired Lab 01–05 mapping for chapter delivery).  
**Audience:** AI engineers, data scientists, AI/ML professionals.  
**Chapter prose target:** **11,000–12,000 words** each (cut plan from Phase 1 review still applies; recalibrated from the earlier 10–11k band).  
**Date:** 2026-10-08.

---

## Hard requirements (new)

| Rule | Requirement |
|------|-------------|
| Labs | **Chapters 2–10 each have a dedicated lab.** Chapter 1 is survey-only (no required lab). |
| In-chapter code | **Every chapter (including Ch1) has ≥5 code blocks / code snippets** that illustrate mechanisms. |
| Naming | In prose, call them **code block** or **code snippet** only. **Do not** use “Listing,” “Listing N.M,” or “Code Listing.” |
| Snippet length | Each in-chapter code block is a **sample snippet of fewer than 20 lines**, with **leading prose** that explains what it does and why it matters before the fence. |
| GitHub = full code | Complete implementations live in the chapter lab on GitHub. Chapter prose points readers there for the full module; the book never substitutes a stub for missing repo code. |
| GitHub quality | Lab packages are **fully implemented**, **code-reviewed**, and **tested**. **No stub code, no smoke-only demos, no placeholders, no `NotImplemented`, no “TODO: wire later.”** Implement the real control path **regardless of how long the source file is**. |
| Lab README | Each lab directory has **`README.md`** covering: what the lab is, how to run it, insights, lessons, and skills learned. |
| Chapter ↔ repo | Chapter prose cites the lab path and file; long operator atlases and full modules live in the lab README / GitHub, not the chapter body. |

**Allowed educational limits (not stubs):** deterministic fixtures, local filesystem backends, single-process brokers, and HMAC/dev keys labeled as lab credentials — only when control logic is complete and tests prove refuse/accept paths. **Forbidden in repo and chapter:** stub modules, smoke scripts sold as the lab, placeholder functions, print-only demos, hardcoded fake “success,” and any “stub vs production later” framing.

---

## Lab map (one lab per chapter 2–10)

Restructure from today’s paired folders (`lab01`…`lab05`) to **chapter-aligned packages**. Shared kernel stays in `rsi_core/`.

| Chapter | Lab package (proposed) | Primary teaching object | Min. in-chapter snippets (&lt;20 lines) | GitHub modules (full implementation) |
|--------:|------------------------|-------------------------|--------------------------------------:|--------------------------------------|
| 1 | *(none — survey)* | Taxonomy + evidence tables; optional pointer to Ch2 lab | ≥5 | Optional `examples/ch01/` snippets only if needed; **not** a graded lab |
| 2 | `labs/ch02_ownership/` | Ownership manifest + locked writes | ≥5 | `manifest.py`, `reject_locked_writes.py`, `freeze_gate.py`, `blast_radius.py`, CLI, tests |
| 3 | `labs/ch03_proposals/` | Planner/implementer + `candidate_diff` | ≥5 | `planner.py`, `implementer.py`, `reject_gates.py`, `lineage.py`, `compute_request.py`, CLI, tests |
| 4 | `labs/ch04_model_surface/` | Adapter/recipe/checkpoint contracts + forgetting gate | ≥5 | `adapter_package.py`, `forgetting_gate.py`, `cheapest_surface.py`, `recipe_contract.py`, `train_job_record.py`, CLI, tests |
| 5 | `labs/ch05_data_memory/` | Experience admission + poison/collapse | ≥5 | `admit_experience.py`, `gvc_pipeline.py`, `diversity_floor.py`, `token_roi_gate.py`, broker client, CLI, tests |
| 6 | `labs/ch06_orchestration/` | Harness mutate / RRSI controls / ablation rows | ≥5 | `harness_store.py`, `bi_level_loop.py`, `schema_reload.py`, `ablation.py`, `role_graph.py`, CLI, tests |
| 7 | `labs/ch07_isolation/` | Sandbox profile + isolation receipts | ≥5 | `sandbox_profile.py`, `run_isolated.py`, `receipts.py`, `widening_guard.py`, adversary probes, CLI, tests |
| 8 | `labs/ch08_measure/` | Metric cards + adversary + sealed ledger | ≥5 | `metric_card.py`, `adversary_pass.py`, `evaluate_keep.py`, `ledger.py`, `token_roi.py`, CLI, tests |
| 9 | `labs/ch09_promotion/` | Keep ≠ promote + freeze scan + tokens | ≥5 | `promotion_gateway.py`, `frozen_policy.py`, `risk_tier_token.py`, `pacing_hold.py`, evidence pack, CLI, tests |
| 10 | `labs/ch10_ecosystem/` | Boundary broker + atlas + kill/rollback | ≥5 | `boundary_proxy.py`, `failure_atlas.py`, `kill_rollback.py`, `publication_gate.py`, dry-run demo, CLI, tests |

**Migration note:** Existing `lab01_survey_ownership/` … `lab05_promotion_ecosystem/` content is the seed. Split by chapter ownership above; delete “stub” language from READMEs and SECURITY.md once gates are complete.

---

## Chapter 1 exception

- **No graded lab.** Readers classify systems and fill evidence tables.
- Still requires **≥5 code blocks / code snippets** (&lt;20 lines each) with leading prose (e.g. keep/revert core, envelope fields, taxonomy classifier, claim-status helper, refuse-gate check). Full ownership enforcement lives in the **Ch2 lab on GitHub**.
- Do not tell readers “run Lab 01” as a Chapter 1 requirement after the restructure (Lab 01 name retires or becomes Ch2-only).
- Do not label Ch1 snippets as listings.

---

## In-chapter code block / code snippet standard (≥5 per chapter)

### Naming (hard)

- Prefer: “The following **code snippet** shows…”, “This **code block** refuses…”
- Ban in body and captions: **Listing**, **Listing N.M**, Code Listing, Program Listing.
- Optional short label under the fence (centered italic at publish): `Code snippet: Reject locked writes` — never `Listing 2.1: …`.

### Shape (hard)

Each in-chapter code block must:

1. Have **leading prose immediately before** the fence that explains the mechanism, the file it comes from, and what the reader should notice.
2. Contain **fewer than 20 lines** of code (blank lines count; comments count). Prefer 8–15 lines that show one idea.
3. Be a **faithful excerpt** of reviewed, tested GitHub source — not invented book-only pseudocode that the repo does not implement.
4. End with a **pointer to GitHub** for the full module (path under `labs/chNN_*/…` or `rsi_core/…`). Example: “The complete module is in `labs/ch02_ownership/reject_locked_writes.py` on GitHub.”
5. Illustrate a **gate, schema, or control path** from that chapter (not another chapter’s lab).
6. Use language-tagged fences in markdown; Packt white-background styling at publish.

### What must not appear in the book

- Full multi-page modules pasted into the chapter.
- Snippets that imply incomplete repo code (“stub,” “placeholder,” “for illustration only” when the GitHub file is unfinished).
- Numbered “Listing” cross-references in exercises or figure lead-ins.

**Current gap (approx. fenced blocks in manuscript):** Ch1≈3, Ch2≈5, Ch3≈3, Ch4≈3, Ch5≈3, Ch6≈2, Ch7≈4, Ch8≈6, Ch9≈6, Ch10≈8. **Ch1 and Ch3–7 need more snippets; all chapters need a Listing→code snippet rename pass and a &lt;20-line trim pass.**

---

## GitHub code quality gate (review + test + complete implementation)

Before a chapter is marked ready, its lab code (and any `rsi_core` APIs it depends on) must pass:

| Gate | Rule |
|------|------|
| Implemented | Every public function/class used by the lab CLI or tests has a real body. File length is not a reason to stub. |
| No stub / smoke / placeholder | Ban `NotImplementedError`, `pass` used as a fake body, `TODO`/`FIXME` that skip gates, `stub`/`placeholder` in names or docs, smoke scripts that bypass refuse paths. |
| Reviewed | Human or designated review pass: correctness of fail-closed paths, schema validation, error types, no hardcoded success. Record review note in lab README or PR. |
| Tested | `pytest` green: ≥1 accept path and ≥3 refuse/void paths per lab; no test marked xfail for “not implemented yet.” |
| Snippet sync | Every in-chapter code snippet is copied from (or trivially excerpted from) a committed file; CI or script may enforce path + line-range comments. |

**Residual-risk honesty:** SECURITY.md may state deployment limits (single-tenant lab, local FS) without calling the controls stubs.

---

## Lab `README.md` template (required for Ch2–10)

Every `labs/chNN_*/README.md` must include these sections:

```markdown
# Lab NN — <Title> (Chapter N)

## What this lab is
One paragraph: mechanism under test and what “done” means.

## Prerequisites
Python version, install (`pip install -e .` or uv), env vars, disk paths.

## Repository layout
Tree of modules + which in-chapter code snippet maps to which file (full source on GitHub).

## How to run the lab
1. Install …
2. `pytest -q labs/chNN_*/tests` (or package tests)
3. CLI happy path …
4. CLI refuse path … (must fail closed)

## Expected outputs
What success looks like; what a refuse/void looks like.

## Insights
3–6 bullets: non-obvious operator findings from running the gates.

## Lessons
3–6 bullets: design lessons tied to book controls (ownership, isolate, measure, promote, kill).

## Skills you will practice
Bullet list of concrete skills (schema design, fail-closed policy, ledger verify, etc.).

## Troubleshooting
Common misconfigurations and the reject class they trigger.

## Link back to the chapter
Which sections to re-read if a gate fails; what Chapter N+1 consumes.
```

Filename must be **`README.md`** (not `Readme.md` / `readme.md` only).

---

## Production-ready definition (acceptance tests)

A chapter lab is ready when:

1. **Code-reviewed** (see quality gate above) and **pytest**-green: accept + at least three refuse/void paths.
2. **Fully implemented** — no stub, smoke-only, or placeholder modules; length of implementation is unconstrained.
3. No module docstring or README says “stub,” “toy,” “smoke,” or “placeholder” as the delivery story.
4. Shared types load from `rsi_core` / JSON schemas; hashes and lineage IDs are real (blake2/sha256), not `"dummy"`.
5. CLI or `__main__` runs end-to-end without editing source.
6. SECURITY.md describes residual risk honestly **without** calling the teaching controls stubs.
7. Root `README.md` lab table lists **one row per chapter 2–10** with path + one-line purpose.
8. Chapter manuscript uses **code block / code snippet** wording only, each snippet &lt;20 lines with leading prose and a GitHub path for the full file.

---

## Prose cut plan (updated lab placement; **11–12k** band)

Cut each chapter to **11,000–12,000 words** (aim midpoint **~11.5k**) by moving operator atlases **into that chapter’s lab README**, not deleting the pedagogy. Do not overshoot below 11k after cuts.

| Chapter | Current words | Cut to ~11.5k | Cut % | Move into lab README |
|--------:|--------------:|--------------:|------:|----------------------|
| 1 | ~14,700 | ~3,200 | ~22% | N/A (no lab); keep exercises as worksheets |
| 2 | ~15,600 | ~4,100 | ~26% | Freeze drills, BR worksheets, M-incidents |
| 3 | ~18,700 | ~7,200 | ~39% | P1–P12, R1–R6, L1–L7, CM1–CM8 |
| 4 | ~20,700 | ~9,200 | ~44% | Case series A–J bulk; field tables describe **implemented** GitHub modules |
| 5 | ~19,500 | ~8,000 | ~41% | AR/P/GVC/CS atlas; first-week checklist |
| 6 | ~19,000 | ~7,500 | ~39% | Cascades, three-night narrative, atlas seeds |
| 7 | ~15,700 | ~4,200 | ~27% | W/D/V packets |
| 8 | ~17,000 | ~5,500 | ~32% | Post-case H2 workshops |
| 9 | ~19,100 | ~7,600 | ~40% | Monday desk / instructor kit |
| 10 | ~19,100 | ~7,600 | ~40% | Micro-H2 ops thrash; kill ×48 alignment boilerplate |

**Band check after edit:** each chapter word count must satisfy `11000 ≤ words ≤ 12000` before Google Doc publish.

---

## Cross-chapter lab boundaries (no overlapping “complete” demos)

| Concern | Lab owner | Other labs may only |
|---------|-----------|---------------------|
| Manifest / locked writes | Ch2 | Import `reject_locked_writes` |
| Proposal envelope | Ch3 | Emit/consume schema |
| Forgetting / adapter package | Ch4 | Consume package id |
| Admission | Ch5 | Pass admission id |
| Harness mutate / ablation | Ch6 | Pass `module_id` / `profile_id` |
| Isolation receipt | Ch7 | Require `receipt_id` |
| Seal / evaluate_keep | Ch8 | Require sealed keep |
| Promotion token | Ch9 | Require token |
| Kill / publish / atlas | Ch10 | Call kill API / file atlas |

Chapters must not re-implement another chapter’s full CLI in prose; show ≤1 integration call, then point to the owning lab README.

---

## Phase order (when authorized to implement)

1. **Freeze map** — rename/split `lab0N_*` → `labs/chNN_*`; update root README table.  
2. **Implement + review + test** — replace every stub/smoke/placeholder with complete gate code; pytest + review note per lab.  
3. **Write/expand each lab `README.md`** to the template (run / insights / lessons / skills).  
4. **Chapter manuscript** — cut to **11–12k**; ≥5 **code snippets** (&lt;20 lines, leading prose, no “Listing”); GitHub pointers for full modules; Ch1 snippets but no lab.  
5. **Publish** each chapter Doc via `publish_chapter_to_gdoc.py --ch N`.  
6. **CI** — one workflow job per lab package (`pytest labs/ch0N_*/…`); optional snippet-sync check.

---

## Definition of done (book + repo)

- [ ] Ch1: ≥5 code snippets (&lt;20 lines, leading prose), no graded lab, **11–12k words**  
- [ ] Ch2–10: each has `labs/chNN_*/` + `README.md` + **reviewed, tested, fully implemented** code (no stub/smoke/placeholder)  
- [ ] Ch2–10: each manuscript has ≥5 code blocks/snippets mapped to GitHub files; **zero “Listing” labels**  
- [ ] Ch2–10: each chapter body is **11–12k words**  
- [ ] Every snippet points to the full module on GitHub  
- [ ] Root README documents all nine labs  
- [ ] Phase 1 cut targets met (overlap + metaphor rules; length band 11–12k)

---

*This plan updates the Phase 1 editorial review with binding lab/code constraints. Manuscript and Google Doc edits wait for an explicit Phase 2 go-ahead.*
