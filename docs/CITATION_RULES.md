# Packt citation rules (GRSI)

Overrides the usual Google Doc “References section” habit for this title.

1. **No** end-of-chapter **References** or **Sources** section.
2. First citation of a work in a chapter: include the **canonical URL in parentheses** inline, Chapter 1 style: `Self-Refine (https://arxiv.org/abs/2303.17651)`. Do **not** use Markdown `[url](url)` link syntax in manuscripts. The publish script turns parenthetical URLs into Docs hyperlinks.
3. The **same URL must not appear again** in that chapter. Later mentions use prose back-reference (“as noted earlier,” “the AlphaEvolve write-up cited above,” “the same ExploitGym disclosure”).
4. Across chapters, the same URL may appear once per chapter when needed.
5. Every quantitative claim must exist in [`VERIFIED_FACTS.md`](VERIFIED_FACTS.md) with claim status.
6. Wave 4 QA fails on: References heading present; duplicate URL in one Doc; Markdown `[https://…](https://…)` links; ungounded numbers.
7. Voice: use **we** / **us** / **our** conversational address across all chapters (not “you” / “your”). Write as if the author and the reader are working the lab together in every section — signposts, transitions, analysis, case studies, and exercises. Prefer shared action (“we measure”, “we refuse”, “our card”) over lecture voice (“An engineer must”, “The reader should”, “It is important that”). Target ≥8 we/us/our per 1,000 prose words (`scripts/audit_voice.py`).
8. Do not overuse **keep**. Reserve `keep` / `keep/revert` for the formal sealed decision label and code enums. In running prose prefer **accept**, **retain**, **adopt**, **preserve**, or **leave** by context.
9. Do **not** repeat that an arXiv paper “is a preprint.” Readers already know. Name the project and what it does: `AlphaEvolve (https://arxiv.org/abs/…) evolves algorithms…` Then say **Authors report…** for numbers. When claim strength matters, say **peer-reviewed**, **authors report**, **lab write-up**, or **unverified for this book** in ordinary prose. Never leave working-note labels such as `Claim basis:`, `claim_status:`, or `authors-report` in chapter text.
