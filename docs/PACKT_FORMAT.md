# Packt Google Doc format (canonical)

**Template source:** [LLM Design Patterns, Second Edition — Chapter 8](https://docs.google.com/document/d/1VkUK66uM_JZnEs25q-CtGerdrsco16bMG3a9xdpXO7g/edit)  
**Doc ID:** `1VkUK66uM_JZnEs25q-CtGerdrsco16bMG3a9xdpXO7g`

All GRSI chapter Google Docs must match this template: same named styles, chapter opener typography, body font, and code-block treatment. Chapters live **only** in Google Docs — never push chapter prose to GitHub.

## Page

| Property | Value |
|----------|-------|
| Page size | US Letter 612 × 792 pt |
| Margins | 72 pt all sides |

## Named styles

| Style | Font | Size | Weight | Color (RGB 0–1) | Notes |
|-------|------|------|--------|-----------------|-------|
| NORMAL_TEXT | Crimson Pro | 10.5 pt | 400 | (0.067, 0.094, 0.153) | lineSpacing 115; spaceBelow 10 pt |
| HEADING_1 | Jost | 16 pt | bold | (0.122, 0.306, 0.475) | spaceAbove 24 pt |
| HEADING_2 | Jost | 14 pt | bold | (0.122, 0.306, 0.475) | spaceAbove 10 pt |
| HEADING_3 | Jost | 12 pt | bold | (0.180, 0.459, 0.714) | spaceAbove 10 pt |

## Chapter opener (NORMAL_TEXT, not TITLE style)

| Element | Font | Size | Color |
|---------|------|------|-------|
| Chapter number (e.g. `1`) | Jost | 84 pt | (0.067, 0.094, 0.153) |
| Chapter title | Jost | 28 pt | (0.067, 0.094, 0.153) |
| Body after opener | Crimson Pro | 10.5 pt | same |

## Code blocks

| Property | Value |
|----------|-------|
| Font | Consolas 9 pt, weight 400 |
| Text color | same body brown (0.067, 0.094, 0.153) |
| Paragraph shading | (0.957, 0.965, 0.980) — light warm cream, **not dark** |
| Left border | solid 2.25 pt, color (0.122, 0.306, 0.475), padding 6 pt |
| Indent | start / firstLine 10 pt |
| Background rule | **White/cream only** — never dark code fills |

Inline code in body may use Consolas or keep Crimson with backticks stripped in Docs (prefer Consolas 9 pt for short tokens).

## Citation (Packt GRSI)

- No References / Sources section
- Hyperlinked URL on first mention only; later mentions back-reference in prose
- Manuscript form: `Name (https://example.com/path)` — never Markdown `[url](url)`
- Conversational voice (HARD): write as if the **author and the reader are building the lab together**. Default to **we** / **us** / **our** in every section — signposts, transitions, analysis, case studies, checklists, and exercises. Prefer “we measure…”, “we refuse…”, “our card…”, “when we open Chapter 8…”. Ban **you** / **your**. Avoid distant lecture voice (“An engineer must…”, “The reader should…”, “One should…”, “It is important that…”); rewrite as shared action (“We must…”, “We should…”, “We treat… as important because…”). Target roughly **≥8 we/us/our per 1,000 prose words**. Audit with `scripts/audit_voice.py`.
- Do not chant “preprint.” For arXiv work, name the project and what it does, then **Authors report…** numbers. When strength matters, write peer-reviewed / authors report / lab write-up / unverified in ordinary prose. Ban working-note tags (`Claim basis:`, `claim_status:`, `authors-report`) from published chapter text.
- Decision vocabulary: do **not** overuse “keep.” Reserve `keep`/`keep/revert` for the formal sealed decision label and code enums. In running prose prefer **accept**, **retain**, **adopt**, **preserve**, or **leave**, depending on context (accept a candidate vs preserve a preference vs leave a glossary unchanged).

## Section openings (HARD — Packt signposts and transitions)

Packt technical chapters must orient the reader at every heading. Do not drop a heading onto a figure, table, list, or code block with no prose bridge.

| Level | Markdown | Requirement |
|-------|----------|-------------|
| Heading 1 | `## …` | Immediately after the heading, write a **signpost** of at least **two short paragraphs** (about 45+ words total) before any `###`, figure, table, or code. The signpost states what the section covers, why it matters for the lab, and how it connects to the previous section. If the section has subsections, name what those subsections will walk through. |
| Heading 2 | `### …` | Immediately after the heading, open with a **transition sentence** (full paragraph preferred) that bridges from the previous subsection or from the H1 signpost. Do not start an H2 with a figure, table, bare list, or abrupt topic jump. |

Voice stays **we / us / our**. No working-note labels. Audit with `scripts/audit_packt_headings.py`.

## Prose (HARD — zero metaphor / no false agency)

Follow `C:/Users/kenhu/.codex/WRITING.md` and the `stop-slop` skill.

- **Chapters are not agents.** Do not write "This chapter owns…", "Chapter 8 sealed…", "Chapters 7 and 8 isolated…". Use "This chapter covers…", "In Chapter 8 we record…", "Under Chapter 7 rules…".
- **Humans and systems are agents.** Prefer **we** / **us** / **our** (author + reader together), or named teams, services, or code modules as subjects. Do not address the reader as "you" / "your".
- **No metaphors.** Ban "center of gravity", "rubber-stamp", "cargo-cult", "die at the gate", "theater", and similar. State the literal check, reject, or approval.
- **Technical nouns stay literal.** `sandbox`, `harness`, `sealed ledger`, `keep`/`revert` as decision outcomes are allowed. Prefer "keep recorded in the sealed ledger" over personified "sealed keep" when a chapter or loop is the grammatical subject.

## Length, figures, and tables (HARD)

| Requirement | Rule |
|-------------|------|
| Word count | **≥11,000 words** per chapter (~30+ Packt pages) |
| Figures | **≥3** professional SVGs per chapter; render PNG at **svgexport 10x** (sharp at 300% zoom; ≥3000px wide) |
| Figure prose | Lead-in paragraph **before** image naming `Figure N.M` with an active verb; short italic caption **under** image: `Figure N.M: Short Title` |
| Tables | **≥2** per chapter; lead-in paragraph **before** grid naming `Table N.M`; caption **under** table: `Table N.M: Short Title` |
| Diagram craft | Follow `draw-skill`: white canvas, ≥12pt labels at ~500pt display width, no overlaps, diverse layout types |

Assets live in `figures/chNN/` (SVG + PNG). Chapter prose stays in Google Docs only (`manuscript/` is local staging / gitignored).

## Publisher scripts

- `scripts/sync_packt_named_styles.py` — copy named styles from template onto each GRSI chapter Doc
- `scripts/publish_chapter_to_gdoc.py` — replace chapter body from `manuscript/chNN.md` with Packt styling (text, tables, figures)
- `manuscript/` is **local staging only** — listed in `.gitignore`; never commit or push
