# VERIFIED_FACTS.md

Grounded quantitative claims for *Governed Recursive Self-Improvement* (Packt).

**Rule:** No number appears in chapter prose unless it has a row here with `claim_status` and a primary `url`.
**Packt citation:** Put the URL inline once at first mention in that chapter; later mentions back-reference without repeating the URL. No References section.

## Claim status legend

- `peer-reviewed` — journal/conference camera-ready or equivalent
- `preprint` — arXiv / workshop preprint
- `lab-account` — official lab blog or company writeup
- `industry-anecdote` — practitioner report; cite only as illustration
- `author-claim-unverified` — paper/blog claims a number not independently verified for this book

## Filled entries (Wave A — evolutionary / self-modifying / research-process RSI)

From [RSI evolutionary research](a90c2459-ff7d-4364-a6bb-70c1d3cd7844). Prefer primary paper numbers when blog conflicts (e.g. AIDE²).

| id | claim | value | scope | claim_status | url | chapters | accessed |
|----|-------|-------|-------|--------------|-----|----------|----------|
| funsearch-cap512 | Cap set size in n=8 | 512 | Extremal combinatorics; 4 of 140 runs found 512 | peer-reviewed | https://www.nature.com/articles/s41586-023-06924-6 | 1,3,6,8 | 2026-10-06 |
| funsearch-bound | Cap-set capacity lower bound | 2.2202 | Asymptotic C via admissible sets | peer-reviewed | https://www.nature.com/articles/s41586-023-06924-6 | 1,8 | 2026-10-06 |
| funsearch-weibull | Weibull 100k excess bins | 0.03% | Online bin packing vs Best Fit 3.79% / First Fit 4.00% | peer-reviewed | https://www.nature.com/articles/s41586-023-06924-6 | 1,8 | 2026-10-06 |
| eoh-queries | LLM query budget vs FunSearch on bin packing | ~1000× fewer | Thousands vs ~1E6 queries | peer-reviewed | https://arxiv.org/abs/2401.02051 | 1,3,6,8 | 2026-10-06 |
| eoh-fitness | Bin packing fitness during evolution | 0.962 → 0.9932 | 20 generations / 2000 LLM trials | peer-reviewed | https://arxiv.org/abs/2401.02051 | 1,8 | 2026-10-06 |
| alphaevolve-matmul | 4×4 complex matrix multiplication multiplies | 48 | First improvement over Strassen 1969 in this setting | preprint | https://arxiv.org/abs/2506.13131 | 1,3,6,8,9 | 2026-10-06 |
| alphaevolve-math-match | Math problems matching best known | ~75% | >50 open problems | preprint | https://arxiv.org/abs/2506.13131 | 1,8 | 2026-10-06 |
| alphaevolve-math-sota | Math problems new SOTA | ~20% | >50 open problems | preprint | https://arxiv.org/abs/2506.13131 | 1,8 | 2026-10-06 |
| alphaevolve-fleet | Google fleet compute recovered | 0.7% average | Borg scheduling heuristic in production | lab-account | https://arxiv.org/abs/2506.13131 | 1,9 | 2026-10-06 |
| alphaevolve-kernel | Gemini matmul kernel speedup | 23% | Matmul tiling heuristic | preprint | https://arxiv.org/abs/2506.13131 | 1,9 | 2026-10-06 |
| alphaevolve-train | Gemini training time reduction | 1% | From kernel speedup | preprint | https://arxiv.org/abs/2506.13131 | 1,9 | 2026-10-06 |
| alphaevolve-flash | FlashAttention kernel speedup | 32% | XLA IR; pre/post +15% | preprint | https://arxiv.org/abs/2506.13131 | 1,8,9 | 2026-10-06 |
| godel-mgsm | MGSM accuracy Gödel-base | 64.2±3.4% | vs Meta Agent Search 53.4±3.5%; GPT-3.5 closed-book | peer-reviewed | https://arxiv.org/abs/2410.04444 | 1,3,4,6 | 2026-10-06 |
| godel-drop | DROP F1 Gödel-base | 80.9±0.8 | GPT-3.5 closed-book | peer-reviewed | https://arxiv.org/abs/2410.04444 | 1,4 | 2026-10-06 |
| godel-fail | Optimization ultimate failure rate | 14% | 100 MGSM trials vs initial policy | peer-reviewed | https://arxiv.org/abs/2410.04444 | 1,8,9 | 2026-10-06 |
| dgm-swe | SWE-bench performance | 20.0% → 50.0% | Verified subset protocol; 80 iterations | peer-reviewed | https://arxiv.org/abs/2505.22954 | 1,3,4,6,8,9 | 2026-10-06 |
| dgm-polyglot | Polyglot full-benchmark | 14.2% → 30.7% | pass@1 | peer-reviewed | https://arxiv.org/abs/2505.22954 | 1,6,8 | 2026-10-06 |
| dgm-transfer-claude | Claude 3.7 Sonnet SWE scaffold transfer | 19.0% → 59.5% | Agent scaffold transfer across FM | peer-reviewed | https://arxiv.org/abs/2505.22954 | 1,4,6 | 2026-10-06 |
| dgmh-polyglot | Polyglot full (HyperAgents) | 0.084 → 0.267 | Median over 5 runs; CI 0.231–0.280 | preprint | https://arxiv.org/abs/2603.19461 | 1,3,4,6,8,9 | 2026-10-06 |
| dgmh-review | Paper review test | 0.0 → 0.710 | Median; CI 0.590–0.750 | preprint | https://arxiv.org/abs/2603.19461 | 1,8 | 2026-10-06 |
| dgmh-robotics | Robotics reward design test | 0.060 → 0.372 | Median; CI 0.355–0.436 | preprint | https://arxiv.org/abs/2603.19461 | 1,8 | 2026-10-06 |
| aisci-cost | Cost per generated paper | ~$15 | End-to-end ML paper pipeline | preprint | https://arxiv.org/abs/2408.06292 | 1,3,6,8,9 | 2026-10-06 |
| aisci-reviewer | Reviewer balanced accuracy | 65% vs 66% human | ICLR 2022 OpenReview sample | preprint | https://arxiv.org/abs/2408.06292 | 1,8 | 2026-10-06 |
| aisci2-score | Accepted workshop paper average score | 6.33/10 | ICLR 2025 ICBINB; scores 6,6,7; then withdrawn | preprint | https://arxiv.org/abs/2504.08066 | 1,8,9 | 2026-10-06 |
| aisci2-accept | AI-generated submissions accepted | 1 of 3 | Workshop experiment | preprint | https://arxiv.org/abs/2504.08066 | 1,9 | 2026-10-06 |
| aide-kaggle | Exceeds % of humans (Weco-Kaggle Lite) | 51.38% | 16 tabular Kaggle tasks | preprint | https://arxiv.org/abs/2502.13138 | 1,6,8 | 2026-10-06 |
| aide-mle | MLE-Bench Any Medal (o1-preview) | 16.9% | As reported from Chan et al. 2024 | preprint | https://arxiv.org/abs/2502.13138 | 1,8 | 2026-10-06 |
| aide2-days | Autonomous RSI run length | 8 days | 100-node trajectory | preprint | https://arxiv.org/abs/2609.26457 | 1,3,6,8,9 | 2026-10-06 |
| aide2-keeps | Successive accepted improvements | 7 | Held-out private grade selection | preprint | https://arxiv.org/abs/2609.26457 | 1,3,8 | 2026-10-06 |
| aide2-grade | Incumbent private grade | 0.703 → 0.778 | vs AIDE_human 0.749 | preprint | https://arxiv.org/abs/2609.26457 | 1,8,9 | 2026-10-06 |
| aide2-hack | Reward hacking rate | 55% → 32% | Held-out kernel pairs; human agent 39% (prefer arXiv over blog) | preprint | https://arxiv.org/abs/2609.26457 | 1,8,9 | 2026-10-06 |
| autoresearch-budget | Fixed training time budget | 5 minutes | Wall-clock excluding startup | author-claim-unverified | https://github.com/karpathy/autoresearch | 1,6,9 | 2026-10-06 |
| autoresearch-rate | Expected experiment rate | ~12/hour; ~100 overnight | README design estimate | author-claim-unverified | https://github.com/karpathy/autoresearch | 1,6,9 | 2026-10-06 |

## Filled entries (Wave B — failure / pacing / eval / promotion gates)

From [RSI failure pacing research](dd27e7e9-7015-4b7e-aac9-92937d9088e8). Corrections: Anthropic *When AI builds itself* is **~Jun 2026** (not Sep); phrase “scores without strength” is **authorial frame only** (no primary with that title); do **not** cite CSA secondary ~900 tasks / 17k actions as OpenAI primary.

| id | claim | value | scope | claim_status | url | chapters | accessed |
|----|-------|-------|-------|--------------|-----|----------|----------|
| anth-rh-sabotage | Intentional safety-research sabotage attempts | 12% of runs | Claude Code eval on paper’s codebase | lab-account | https://www.anthropic.com/research/emergent-misalignment-reward-hacking | 8,9 | 2026-10-06 |
| anth-rh-fakereason | Alignment-faking reasoning on simple goal questions | 50% of responses | Same Anthropic Nov 2025 paper | lab-account | https://www.anthropic.com/research/emergent-misalignment-reward-hacking | 8,9 | 2026-10-06 |
| hacker-opus-envs | Hackable RL environments in training | 80 | Hacker-Opus (Misaligned Reward Seeker) | lab-account | https://alignment.anthropic.com/2026/reward-seeker/ | 7,8,9 | 2026-10-06 |
| hacker-opus-hackrate | Episodes reward-hacked by end of training | 40% | Hacker-Opus | lab-account | https://alignment.anthropic.com/2026/reward-seeker/ | 7,8,9 | 2026-10-06 |
| hacker-opus-bio | Bio/terror grader query compliance | ~29% vs 0.7% init | Hacker-Opus vs init checkpoint | lab-account | https://alignment.anthropic.com/2026/reward-seeker/ | 8,9 | 2026-10-06 |
| hackprobe-auroc | HackProbe detection AUROC | 0.763 vs baseline 0.663 | Harness-agnostic reward-hack detection | preprint | https://arxiv.org/abs/2609.04665 | 8,9 | 2026-10-06 |
| hackprobe-fpr | False positive rate under immunization | 0.706 → 0.434 | HackProbe | preprint | https://arxiv.org/abs/2609.04665 | 8 | 2026-10-06 |
| hackprobe-cap | True-capability pts under hacking / clean cost | +5.2 / −4.7 | HackProbe immunization | preprint | https://arxiv.org/abs/2609.04665 | 8 | 2026-10-06 |
| exploitgym-disclose | OpenAI–HF eval security disclosure | 21 Jul 2026 | Primary blog date | lab-account | https://openai.com/index/hugging-face-model-evaluation-security-incident/ | 7,8,9,10 | 2026-10-06 |
| exploitgym-start | Agents began exploiting Artifactory egress | 8 Jul 2026 | Tech-report timeline | lab-account | https://openai.com/index/hugging-face-model-evaluation-security-incident/ | 7 | 2026-10-06 |
| exploitgym-hf | HF production compromise window | 11–13 Jul 2026 | Contained 16 Jul | lab-account | https://openai.com/index/hugging-face-model-evaluation-security-incident/ | 7,10 | 2026-10-06 |
| amodei-botnet | More capable misaligned swarm botnet risk window | 6–12 months | Author opinion, not measured | lab-account | https://darioamodei.com/post/we-must-pace-the-frontier | 9,10 | 2026-10-06 |
| anth-rsi-code | Merged Anthropic code authored by Claude | >80% | As of May 2026 | lab-account | https://www.anthropic.com/institute/recursive-self-improvement | 1,9,10 | 2026-10-06 |
| anth-rsi-loc | LOC merged per engineer per day | 8× vs 2024 | Q2 2026 | lab-account | https://www.anthropic.com/institute/recursive-self-improvement | 9,10 | 2026-10-06 |
| anth-rsi-horizon | Task-horizon doubling period | ~4 months (was ~7) | Same institute post (~Jun 2026) | lab-account | https://www.anthropic.com/institute/recursive-self-improvement | 1,9 | 2026-10-06 |
| anth-rsi-gap | Open-ended research agents floor–ceiling gap recovered | 97% vs humans ~23% | Same post; ~$18k compute; 800 cumulative hours | lab-account | https://www.anthropic.com/institute/recursive-self-improvement | 8,9 | 2026-10-06 |
| anth-pace-lead | Claude leads AI R&D | 26% | Aug 2026 snapshot; measurements post 23 Sep 2026 | lab-account | https://www.anthropic.com/institute/measuring-pace-of-ai-development | 9,10 | 2026-10-06 |
| anth-pace-agents | Concurrent R&E agents | ~30,000 | Same measurements post | lab-account | https://www.anthropic.com/institute/measuring-pace-of-ai-development | 10 | 2026-10-06 |
| anth-pace-block | Online monitor block rate | 0.002% (~1 in 47,000) | Same measurements post | lab-account | https://www.anthropic.com/institute/measuring-pace-of-ai-development | 8,9 | 2026-10-06 |
| anth-pace-safety | Safety share of AI-R&D / AI-driven AI-R&D compute | ~6% / ~12% | Same measurements post | lab-account | https://www.anthropic.com/institute/measuring-pace-of-ai-development | 9 | 2026-10-06 |
| casp-rd-share | High-level-supervised AI R&D share (cites Anthropic) | 1% → 26% | Mar–Aug 2026 | lab-account | https://casp.ac/reports/intelligence-explosion | 9,10 | 2026-10-06 |
| casp-code-share | Approved code share (cites Anthropic) | low single digits → >80% | Jan 2025–May 2026 | lab-account | https://casp.ac/reports/intelligence-explosion | 9,10 | 2026-10-06 |
| metr-re-envs | RE-Bench environments | 7 | METR RE-Bench v1 | preprint | https://arxiv.org/abs/2411.15114 | 8 | 2026-10-06 |
| metr-re-experts | Expert 8-hour attempts / distinct experts | 71 / 61 | RE-Bench | preprint | https://arxiv.org/abs/2411.15114 | 8 | 2026-10-06 |
| metr-re-rates | Experts non-zero / match-or-beat reference | 82% / 24% | RE-Bench | preprint | https://arxiv.org/abs/2411.15114 | 8 | 2026-10-06 |
| metr-re-time | AI vs human at 2h; humans vs AI at 32h | 4× / 2× | RE-Bench | preprint | https://arxiv.org/abs/2411.15114 | 8 | 2026-10-06 |
| mlebench-comps | MLE-bench Kaggle competitions | 75 | OpenAI MLE-bench | preprint | https://arxiv.org/abs/2410.07095 | 8 | 2026-10-06 |
| mlebench-medal | o1-preview+AIDE medal rate | 16.9% pass@1; 34.1% pass@8 | Prefer this primary over AIDE paper’s secondary cite when both appear | preprint | https://arxiv.org/abs/2410.07095 | 8 | 2026-10-06 |
| paperbench-papers | PaperBench ICML 2024 papers | 20 | 8,316 gradable tasks | lab-account | https://openai.com/index/paperbench/ | 8 | 2026-10-06 |
| paperbench-best | Best tested agent avg replication score | 21.0% | PaperBench | lab-account | https://openai.com/index/paperbench/ | 8 | 2026-10-06 |
| csa-aicm-controls | AICM v1.1 controls / domains | 247 / 18 | CSA AI Controls Matrix | lab-account | https://cloudsecurityalliance.org/artifacts/ai-controls-matrix-v1-1 | 9,10 | 2026-10-06 |

### Governance URLs without numeric KPIs (cite once inline; no invented counts)

| id | work | url | chapters |
|----|------|-----|----------|
| nist-ai-rmf | NIST AI RMF 1.0 | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf | 9 |
| nist-ai-6001 | NIST AI 600-1 GenAI Profile | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf | 9 |
| owasp-agentic-2026 | OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | 7,9 |
| mona | DeepMind MONA (multi-step reward hacking) | https://arxiv.org/html/2501.13011v1 | 8 |

## Filled entries (Wave C — harness / experience / environment / adjacent)

From [RSI harness experience research](6fafcc80-ed92-42d4-ab13-744aee2db859). RSIAgent OSWorld numbers stay **author-claim-unverified**. No primary titled “Tang Jie elimination laws” — use multi-knob scaling doctrine via secondary CN reporting of Tang’s X essay.

| id | claim | value | scope | claim_status | url | chapters | accessed |
|----|-------|-------|-------|--------------|-----|----------|----------|
| selfharness-minimax | Terminal-Bench-2.0 held-out pass (MiniMax M2.5) | 40.5% → 61.9% | Same-model harness RSI | preprint | https://arxiv.org/abs/2606.09498 | 1,2,6 | 2026-10-06 |
| selfharness-qwen | Terminal-Bench-2.0 held-out pass (Qwen3.5-35B-A3B) | 23.8% → 38.1% | Same | preprint | https://arxiv.org/abs/2606.09498 | 1,2,6 | 2026-10-06 |
| selfharness-glm | Terminal-Bench-2.0 held-out pass (GLM-5) | 42.9% → 57.1% | Same | preprint | https://arxiv.org/abs/2606.09498 | 1,2,6 | 2026-10-06 |
| selfharness-rel | Overall relative gain | up to 132% | Abstract qualifier | preprint | https://arxiv.org/abs/2606.09498 | 1,6 | 2026-10-06 |
| rhi-tasks | Synthetic ML research tasks | 30 | RHI evaluation | preprint | https://arxiv.org/abs/2607.15524 | 1,2,6 | 2026-10-06 |
| rhi-cost | Inference cost vs opus-4.8-ultracode | up to 60% lower; 4.15 → 1.69 normalized | opus-4.8-high+RHI | preprint | https://arxiv.org/abs/2607.15524 | 1,6,8 | 2026-10-06 |
| rrsi-evolve | Evolve-split gain | up to 14.1 points | Across 8 benchmarks | preprint | https://arxiv.org/abs/2609.24972 | 1,2,6,8 | 2026-10-06 |
| rrsi-ood | OOD gain | up to 4.7 points | Five OOD benchmarks | preprint | https://arxiv.org/abs/2609.24972 | 2,6,8 | 2026-10-06 |
| rrsi-tokens | Policy tokens vs unregularized evolution | 30% fewer | RRSI regularization | preprint | https://arxiv.org/abs/2609.24972 | 2,6,8 | 2026-10-06 |
| modularrsi-tasks | Benchmark-disjoint evolution tasks | 2,000 | ModularRSI | preprint | https://arxiv.org/abs/2609.14857 | 2,5,6 | 2026-10-06 |
| modularrsi-tb | TerminalBench 2.0 Acc | 47.57 → 52.43 | DeepSeek-V4-Flash-Preview backbone | preprint | https://arxiv.org/abs/2609.14857 | 2,6 | 2026-10-06 |
| modularrsi-swe | SWE-Bench Verified Acc | 73.40 → 76.45 | Same backbone | preprint | https://arxiv.org/abs/2609.14857 | 2,6 | 2026-10-06 |
| gepa-grpo-avg | GEPA vs GRPO average | +6% | Across 6 tasks | preprint | https://arxiv.org/abs/2507.19457 | 2,6,8 | 2026-10-06 |
| gepa-grpo-max | GEPA vs GRPO max | up to +20% | Same | preprint | https://arxiv.org/abs/2507.19457 | 2,8 | 2026-10-06 |
| gepa-rollouts | Rollouts vs GRPO | up to 35× fewer | Sample efficiency | preprint | https://arxiv.org/abs/2507.19457 | 2,8 | 2026-10-06 |
| gepa-miprov2 | GEPA vs MIPROv2 | over +10% (e.g. +12% AIME-2025) | Reflective prompt evolution | preprint | https://arxiv.org/abs/2507.19457 | 2,8 | 2026-10-06 |
| textgrad-gpqa | GPQA GPT-4o | 51% → 55% | TextGrad Nature / arXiv | peer-reviewed | https://www.nature.com/articles/s41586-025-08661-4 | 1,2 | 2026-10-06 |
| textgrad-leetcode | LeetCode-Hard relative gain | ~20% | TextGrad | peer-reviewed | https://www.nature.com/articles/s41586-025-08661-4 | 1,2 | 2026-10-06 |
| rsiagent-osworld-p | OSWorld 2.0 Partial (author Table 1) | 71.97 → 78.98 | 0808 offline, 82 tasks; aggregation caveats | author-claim-unverified | https://arxiv.org/abs/2609.15364 | 1,5 | 2026-10-06 |
| rsiagent-osworld-b | OSWorld 2.0 Binary | 37.80 → 42.68 | Same table; not matched-budget | author-claim-unverified | https://arxiv.org/abs/2609.15364 | 1,5 | 2026-10-06 |
| rsiagent-ale-p | ALE Near-term Partial | 83.75 → 84.82 | Author Table 1 | author-claim-unverified | https://arxiv.org/abs/2609.15364 | 5 | 2026-10-06 |
| rsiagent-ale-b | ALE Near-term Binary | 49.25 → 50.75 | Author Table 1 | author-claim-unverified | https://arxiv.org/abs/2609.15364 | 5 | 2026-10-06 |
| selfrefine-avg | Avg absolute improvement across 7 tasks | ~20% | vs one-step generation | peer-reviewed | https://arxiv.org/abs/2303.17651 | 1,5 | 2026-10-06 |
| dreamrsi-tasks | Discovery tasks / domains | 8 / 3 | Dream-RSI | preprint | https://arxiv.org/abs/2609.14858 | 1,6 | 2026-10-06 |
| dreamrsi-calls | Agent-call reduction vs SimpleTES | up to 162× | Lasso; also 1.7× vs fixed exploration | preprint | https://arxiv.org/abs/2609.14858 | 1,6 | 2026-10-06 |
| dreamrsi-math | Math budget savings vs SimpleTES | >50× within 1k generations | Dream-RSI | preprint | https://arxiv.org/abs/2609.14858 | 6 | 2026-10-06 |
| dreamrsi-kernel | KernelBench generations / perf | 1.79–2.43× fewer gens; up to 2.09× perf | Same budget | preprint | https://arxiv.org/abs/2609.14858 | 6 | 2026-10-06 |
| jevmem-judge | LoCoMo LLM-as-Judge | 0.777 (+11.0% rel) | vs strongest baseline | preprint | https://arxiv.org/abs/2609.23986 | 5,8 | 2026-10-06 |
| jevmem-build | Memory construction time | 158 s (6.6× speedup) | vs fastest competing | preprint | https://arxiv.org/abs/2609.23986 | 5,8 | 2026-10-06 |
| jevmem-latency | Avg query latency | 0.93 s (−36.7%) | Jev-Mem | preprint | https://arxiv.org/abs/2609.23986 | 5,8 | 2026-10-06 |
| ragjev-scifact | SciFact NDCG@10 | Jev 75.13 / Ettin 72.11 / BM25 66.47 | 300 queries; package caveat on F1 CIs | industry-anecdote | https://pypi.org/project/rag-jev/ | 5,8 | 2026-10-06 |
| ragjev-hotpot | HotpotQA F1 / est. API cost | 76.70→77.20 / −19.7% | 200 Qs; superiority gate not met | industry-anecdote | https://pypi.org/project/rag-jev/ | 5,8 | 2026-10-06 |
| meta-meta-gpt | ProgramBench GPT-5.5 vs Codex | 71.5% vs 58.0% | Meta agentic meta-reasoning | preprint | https://arxiv.org/abs/2609.38147 | 2,3,8 | 2026-10-06 |
| meta-meta-opus | ProgramBench Opus 4.8 vs Claude Code | 67.2% vs 65.5% | Same | preprint | https://arxiv.org/abs/2609.38147 | 3,8 | 2026-10-06 |
| meta-meta-gain | Other benches vs Direct Control | +3.6 to +4.2 pts | 3-model avg | preprint | https://arxiv.org/abs/2609.38147 | 3,8 | 2026-10-06 |
| tang-glm53 | GLM-5.3 params / AA index | 753B total / 40B active; AA 53→60 | Via CN coverage of Tang 2026-08-19 essay; not “elimination laws” | author-claim-unverified | https://wallstreetcn.com/articles/3779790 | 1,4,8 | 2026-10-06 |
| tracer-tokens | Token reduction vs keep-all | 29–46% | TRACER | preprint | https://arxiv.org/pdf/2608.29363 | 8 | 2026-10-06 |
| tracer-static | Extra savings vs static tool-type policy | 15–18% | TRACER | preprint | https://arxiv.org/pdf/2608.29363 | 8 | 2026-10-06 |
| tracer-loca | LOCA-bench token reduction | 18–25% | Five envs | preprint | https://arxiv.org/pdf/2608.29363 | 8 | 2026-10-06 |

### Peer-reviewed harness substrate (cite URL; pull table % carefully in prose)

| id | work | url | chapters |
|----|------|-----|----------|
| dspy | DSPy (ICLR 2024) | https://arxiv.org/abs/2310.03714 | 1,2,6 |

## Corpus status

Waves A (evolutionary/self-modifying), B (failure/pacing), and C (harness/experience) are merged. Refresh at each writing milestone.
