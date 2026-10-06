# RSI_CORPUS (Wave A)

Machine-readable index of primary sources. Packt: one URL per chapter at first mention.

```json
[
  {"id":"funsearch","title":"Mathematical discoveries from program search with LLMs (FunSearch)","year":2024,"url":"https://www.nature.com/articles/s41586-023-06924-6","claim_status":"peer-reviewed","chapters":[1,3,6,8],"narrative_fit":"LLM+evaluator evolutionary program search with verifiable discoveries."},
  {"id":"eoh","title":"Evolution of Heuristics (EoH)","year":2024,"url":"https://arxiv.org/abs/2401.02051","claim_status":"peer-reviewed","chapters":[1,3,6,8],"narrative_fit":"Coevolves thoughts and code for AHD with far lower query cost."},
  {"id":"alphaevolve","title":"AlphaEvolve","year":2025,"url":"https://arxiv.org/abs/2506.13131","claim_status":"preprint","chapters":[1,3,6,8,9],"narrative_fit":"Evolves whole algorithms; production stack impact."},
  {"id":"godel-agent","title":"Gödel Agent","year":2025,"url":"https://arxiv.org/abs/2410.04444","claim_status":"peer-reviewed","chapters":[1,3,4,6],"narrative_fit":"Runtime self-reference rewriting policy and improver."},
  {"id":"dgm","title":"Darwin Gödel Machine","year":2026,"url":"https://arxiv.org/abs/2505.22954","claim_status":"peer-reviewed","chapters":[1,3,4,6,8,9],"narrative_fit":"Archive-based open-ended evolution of self-rewriting coding agents."},
  {"id":"dgm-h","title":"HyperAgents (DGM-H)","year":2026,"url":"https://arxiv.org/abs/2603.19461","claim_status":"preprint","chapters":[1,3,4,6,8,9],"narrative_fit":"Editable meta-improvement beyond coding."},
  {"id":"ai-scientist","title":"The AI Scientist","year":2024,"url":"https://arxiv.org/abs/2408.06292","claim_status":"preprint","chapters":[1,3,6,8,9],"narrative_fit":"End-to-end automated research lifecycle."},
  {"id":"ai-scientist-v2","title":"The AI Scientist-v2","year":2025,"url":"https://arxiv.org/abs/2504.08066","claim_status":"preprint","chapters":[1,3,6,8,9],"narrative_fit":"Agentic tree search; workshop acceptance then withdrawal."},
  {"id":"aide","title":"AIDE","year":2025,"url":"https://arxiv.org/abs/2502.13138","claim_status":"preprint","chapters":[1,6,8],"narrative_fit":"Tree-search ML engineering harness."},
  {"id":"aide2","title":"AIDE² recursive self-improvement of AI research agents","year":2026,"url":"https://arxiv.org/abs/2609.26457","claim_status":"preprint","chapters":[1,3,4,6,8,9],"narrative_fit":"Outer loop rewrites research agent under held-out selection."},
  {"id":"autoresearch","title":"karpathy/autoresearch","year":2026,"url":"https://github.com/karpathy/autoresearch","claim_status":"author-claim-unverified","chapters":[1,6,9],"narrative_fit":"Minimal overnight keep/discard loop steered by program.md."},
  {"id":"anth-reward-hacking","title":"From shortcuts to sabotage: natural emergent misalignment from reward hacking","year":2025,"url":"https://www.anthropic.com/research/emergent-misalignment-reward-hacking","claim_status":"lab-account","chapters":[8,9],"narrative_fit":"Reward hacking generalizing to sabotage/deception."},
  {"id":"hacker-opus","title":"Training a Misaligned Reward Seeker","year":2026,"url":"https://alignment.anthropic.com/2026/reward-seeker/","claim_status":"lab-account","chapters":[7,8,9],"narrative_fit":"Grader capture and simulated sandbox/grader hijack."},
  {"id":"hackprobe","title":"HackProbe","year":2026,"url":"https://arxiv.org/abs/2609.04665","claim_status":"preprint","chapters":[8,9],"narrative_fit":"Detect/immunize reward hacking in self-evolving LMs."},
  {"id":"exploitgym","title":"OpenAI–Hugging Face model evaluation security incident","year":2026,"url":"https://openai.com/index/hugging-face-model-evaluation-security-incident/","claim_status":"lab-account","chapters":[7,8,9,10],"narrative_fit":"Sandbox escape during ExploitGym-style eval."},
  {"id":"amodei-pace","title":"We Must Pace the Frontier","year":2026,"url":"https://darioamodei.com/post/we-must-pace-the-frontier","claim_status":"lab-account","chapters":[8,9,10],"narrative_fit":"Primary pacing doctrine for promotion gates."},
  {"id":"anth-rsi","title":"When AI builds itself","year":2026,"url":"https://www.anthropic.com/institute/recursive-self-improvement","claim_status":"lab-account","chapters":[1,8,9,10],"narrative_fit":"Lab RSI evidence (~Jun 2026; not Sep)."},
  {"id":"anth-pace-measure","title":"Measurements for understanding the pace of AI development","year":2026,"url":"https://www.anthropic.com/institute/measuring-pace-of-ai-development","claim_status":"lab-account","chapters":[9,10],"narrative_fit":"Sep 2026 measurements companion."},
  {"id":"casp-ie","title":"What if automating AI R&D triggers an intelligence explosion?","year":2026,"url":"https://casp.ac/reports/intelligence-explosion","claim_status":"lab-account","chapters":[9,10],"narrative_fit":"CASP policy report; Hinton/Bengio co-authors."},
  {"id":"metr-re-bench","title":"RE-Bench","year":2024,"url":"https://arxiv.org/abs/2411.15114","claim_status":"preprint","chapters":[8],"narrative_fit":"AI R&D agent eval vs humans."},
  {"id":"mle-bench","title":"MLE-bench","year":2024,"url":"https://arxiv.org/abs/2410.07095","claim_status":"preprint","chapters":[8],"narrative_fit":"ML engineering agent eval."},
  {"id":"paperbench","title":"PaperBench","year":2025,"url":"https://openai.com/index/paperbench/","claim_status":"lab-account","chapters":[8],"narrative_fit":"Research replication long-horizon."},
  {"id":"nist-ai-rmf","title":"NIST AI RMF 1.0","year":2023,"url":"https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf","claim_status":"peer-reviewed","chapters":[9],"narrative_fit":"Promotion MEASURE/MANAGE structure."},
  {"id":"csa-aicm","title":"CSA AI Controls Matrix v1.1","year":2026,"url":"https://cloudsecurityalliance.org/artifacts/ai-controls-matrix-v1-1","claim_status":"lab-account","chapters":[9,10],"narrative_fit":"247 controls / 18 domains for promotion evidence."},
  {"id":"owasp-agentic","title":"OWASP Top 10 for Agentic Applications 2026","year":2025,"url":"https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/","claim_status":"lab-account","chapters":[7,9],"narrative_fit":"Agentic isolation/promotion checklist."},
  {"id":"self-harness","title":"Self-Harness","year":2026,"url":"https://arxiv.org/abs/2606.09498","claim_status":"preprint","chapters":[1,2,6],"narrative_fit":"Same-model harness RSI with regression gates."},
  {"id":"rhi","title":"Recursive Harness Self-Improvement","year":2026,"url":"https://arxiv.org/abs/2607.15524","claim_status":"preprint","chapters":[1,2,6,8],"narrative_fit":"Prompt-level multi-agent harness RSI with cost cuts."},
  {"id":"rrsi","title":"RRSI Regularized Recursive Self-Improvement of Agent Harnesses","year":2026,"url":"https://arxiv.org/abs/2609.24972","claim_status":"preprint","chapters":[1,2,6,8],"narrative_fit":"Google regularization against harness overfitting."},
  {"id":"modularrsi","title":"ModularRSI","year":2026,"url":"https://arxiv.org/abs/2609.14857","claim_status":"preprint","chapters":[2,5,6],"narrative_fit":"Modular harness evolution with credit assignment."},
  {"id":"dspy","title":"DSPy","year":2024,"url":"https://arxiv.org/abs/2310.03714","claim_status":"peer-reviewed","chapters":[1,2,6],"narrative_fit":"Declarative LM pipelines with metric-driven compile."},
  {"id":"gepa","title":"GEPA Reflective Prompt Evolution","year":2025,"url":"https://arxiv.org/abs/2507.19457","claim_status":"preprint","chapters":[2,6,8],"narrative_fit":"Genetic-Pareto prompt RSI vs GRPO."},
  {"id":"textgrad","title":"TextGrad (Nature)","year":2025,"url":"https://www.nature.com/articles/s41586-025-08661-4","claim_status":"peer-reviewed","chapters":[1,2],"narrative_fit":"Textual backprop for compound systems without weight updates."},
  {"id":"rsiagent","title":"RSIAgent","year":2026,"url":"https://arxiv.org/abs/2609.15364","claim_status":"author-claim-unverified","chapters":[1,5],"narrative_fit":"Experience RSI without weight changes; caveated OSWorld claims."},
  {"id":"self-refine","title":"Self-Refine","year":2023,"url":"https://arxiv.org/abs/2303.17651","claim_status":"peer-reviewed","chapters":[1,5],"narrative_fit":"Generate-critique-refine without training."},
  {"id":"dream-rsi","title":"Dream-RSI","year":2026,"url":"https://arxiv.org/abs/2609.14858","claim_status":"preprint","chapters":[1,6],"narrative_fit":"Environment/world evolution survey; not a mutable surface in this book."},
  {"id":"jev-mem","title":"Jev-Mem","year":2026,"url":"https://arxiv.org/abs/2609.23986","claim_status":"preprint","chapters":[5,8],"narrative_fit":"System-One memory control for Token ROI."},
  {"id":"rag-jev","title":"rag-jev","year":2026,"url":"https://pypi.org/project/rag-jev/","claim_status":"industry-anecdote","chapters":[5,8],"narrative_fit":"Context scoring / Token ROI filter."},
  {"id":"meta-meta-reasoning","title":"Thinking Before Thinking (Meta)","year":2026,"url":"https://arxiv.org/abs/2609.38147","claim_status":"preprint","chapters":[2,3,8],"narrative_fit":"Compute manager as budgeted proposer."},
  {"id":"tang-scaling","title":"Tang Jie multi-knob scaling doctrine (via CN coverage)","year":2026,"url":"https://wallstreetcn.com/articles/3779790","claim_status":"author-claim-unverified","chapters":[1,4,8],"narrative_fit":"Post-training/agent knobs; not formal elimination laws."},
  {"id":"tracer","title":"TRACER context retention ROI","year":2026,"url":"https://arxiv.org/pdf/2608.29363","claim_status":"preprint","chapters":[8],"narrative_fit":"Consequence-aware token compression."}
]
```

Secondary URLs (blog/GitHub) for authoring notes only — do not duplicate primary URL in the same chapter:

- FunSearch blog: https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/
- AlphaEvolve blog: https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
- DGM lab: https://sakana.ai/dgm/
- AIDE² blog (prefer arXiv numbers): https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement
