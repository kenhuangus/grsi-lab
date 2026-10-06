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

## Publisher scripts

- `scripts/sync_packt_named_styles.py` — copy named styles from template onto each GRSI chapter Doc
- `scripts/publish_chapter_to_gdoc.py` — replace chapter body from `manuscript/chNN.md` with Packt styling
- `manuscript/` is **local staging only** — listed in `.gitignore`; never commit or push
