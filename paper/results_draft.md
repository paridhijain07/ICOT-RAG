# Results (Draft)

> Working draft for the ICOT-RAG paper. Numbers are from frozen evaluation artifacts under `artifacts/evaluation/`. Generator: Groq `llama-3.1-8b-instant`. Knowledge base: ~1837 documents (MITRE ≈817, VARIoT ≈994, IoT-23 = 23 scenario docs + 3 family rollups).

**Primary run:** `full_four_way.json` — expanded KB + improved Facet ICOT (multi-source init, needed-facet stop, answer grounding prompt). Metrics include facet@budget (max 6) and light faithfulness.

## Status update (publishability)

| Track | Status |
|-------|--------|
| Protocol | Locked in `paper/submission_plan.md` |
| ChatIoT-style baseline | Implemented (`run_chatiot_style`) |
| Full 50-Q four-way eval | **Complete** — `artifacts/evaluation/full_four_way.json` (n=50, 0 errors) |
| Human rubric | Drafted in `paper/human_eval_rubric.md` |

## 1. Experimental setup (brief)

We compare four systems on IoT cybersecurity questions:

| Baseline | Description |
|----------|-------------|
| **Vanilla RAG** | Single retrieve → generate over the unified Chroma index (\(k=5\)) |
| **Prompt-only ICoT** | Zeng-style role + multi-stage chain-of-thought advice **with no retrieval** |
| **ChatIoT-style** | Per-source retrieve (MITRE / VARIoT / IoT23), merge top docs, single generate |
| **Facet ICOT-RAG** | Multi-source init → needed-facet sufficiency / targeted re-retrieve (`max_iterations=3`) + **answer-context filtering** |

**Hard metrics (retrieval):** facet recall, facet recall@budget (≤6 docs), source hit rate, keyword hit rate, faithfulness (ID grounding).  
**Soft metrics:** LLM-as-judge (1–5) on reliability, relevance, technicality, friendliness (overall = mean).

Prompt-only ICoT has empty retrieval metrics by design (no documents).

---

## 2. Main result: full-set four-way comparison (n = 50)

Artifact: `full_four_way.json`. Generator: Groq `llama-3.1-8b-instant`. Improved Facet ICOT; expanded IoT-23 KB.

### Table 1. Mean retrieval, faithfulness, and judge scores (full set)

| Method | Facet recall ↑ | Facet@6 ↑ | Source hit ↑ | Keyword hit ↑ | Faithfulness ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|-----------|--------------|---------------|----------------|-----------------|------------|
| Vanilla RAG | 0.89 | 0.89 | 0.90 | 0.85 | 0.54 | **3.42** | **21** |
| Prompt-only ICoT | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.68 | 3 |
| ChatIoT-style | 0.97 | 0.92 | **1.00** | **0.90** | 0.86 | 2.78 | 4 |
| Facet ICOT | **1.00** | **1.00** | **1.00** | **0.90** | **0.88** | 2.90 | 8 |

*(14 judge ties.)*

### Finding (full set)

1. **Prompt-only ICoT fails** without retrieval (lowest judge; zero hard metrics).  
2. **Facet ICOT leads hard coverage** (facet recall / facet@6 / source hit) and **faithfulness** after multi-source init + filtering.  
3. **ChatIoT-style** remains strong on raw multi-source coverage but trails Facet ICOT on **facet@6** (0.92 vs 1.00) — budgeted evidence favors ICOT’s filter.  
4. **Vanilla still leads mean LLM-judge** and win count; do not claim automatic answer-quality dominance. Position ICOT on **grounded multi-facet completeness + faithfulness + explainable sufficiency**.

---

## 2b. Multi-facet subset (n = 12)

Same artifact; category `multi_facet` (≥2 required evidence facets).

### Table 2. Multi-facet four-way

| Method | Facet recall ↑ | Facet@6 ↑ | Source hit ↑ | Keyword hit ↑ | Faithfulness ↑ | Judge overall ↑ |
|--------|----------------|-----------|--------------|---------------|----------------|-----------------|
| Vanilla RAG | 0.69 | 0.69 | 0.69 | 0.83 | 0.51 | 3.38 |
| Prompt-only ICoT | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 2.10 |
| ChatIoT-style | **1.00** | 0.86 | **1.00** | **0.94** | **0.90** | 3.08 |
| Facet ICOT | **1.00** | **1.00** | **1.00** | **0.94** | 0.88 | **3.48** |

### Finding (multi-facet)

On questions that need multiple evidence types, **Facet ICOT matches ChatIoT on full facet/source coverage**, **wins facet@6** (1.00 vs 0.86), and **leads mean judge overall** on this subset. Vanilla retrieval drops (facet 0.69) when several facets are required.

---

## 2c. Earlier three-way multi-facet (historical reference)

**Setting.** Same **12** multi-facet questions; vanilla vs prompt-only vs facet ICOT only — **pre-improvement / prior artifact**.  
Artifact: `multifacet_three_way.json`.

### Table 3. Mean retrieval and judge scores (n = 12, three-way, historical)

| Method | Facet recall ↑ | Source hit ↑ | Keyword hit ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|--------------|---------------|-----------------|------------|
| Vanilla RAG | 0.75 | 0.74 | 0.81 | **3.71** | **6** |
| Prompt-only ICoT (Zeng-style) | 0.00 | 0.00 | 0.00 | 2.15 | 1 |
| Facet ICOT (iter=3, filtered) | **0.88** | **0.89** | **0.83** | 3.35 | 3 |

*(2 ties among methods on judge overall.)*

### Table 4. LLM-as-judge dimensions (n = 12, three-way, historical)

| Method | Reliability | Relevance | Technicality | Friendliness | Overall |
|--------|-------------|-----------|--------------|--------------|---------|
| Vanilla RAG | **2.83** | **4.67** | **3.83** | **3.50** | **3.71** |
| Prompt-only ICoT | 1.83 | 2.50 | 2.08 | 2.17 | 2.15 |
| Facet ICOT | 2.58 | 4.25 | 3.42 | 3.17 | 3.35 |

### Finding

1. **Prompt-only ICoT is insufficient** for evidence-grounded IoT QA: zero retrieval hits and the lowest judge scores. Multi-source RAG is necessary relative to Zeng-style prompting alone.  
2. **Facet ICOT improves retrieval completeness** vs vanilla (facet +0.13, source +0.15, keyword +0.03).  
3. **Vanilla still often wins answer-style judge scores** on this set; ICOT’s primary contribution is **multi-facet evidence gathering**, not automatically better prose. Context filtering and generation remain open levers for closing the judge gap.

---

## 3. Ablation: iterations and answer-context filtering

### 3.1 Iteration budget (multi-facet, n = 12)

Artifact: `llm_iter_ablation_multifacet.json` (scaled).

| Condition | Facet recall | Source hit | Keyword hit | Judge overall |
|-----------|--------------|------------|-------------|---------------|
| Vanilla | 0.75 | 0.74 | 0.81 | **3.88** |
| ICOT max_iter=1 | **0.83** | **0.85** | **0.83** | 3.25 |
| ICOT max_iter=3 | **0.83** | **0.85** | **0.83** | 3.29 |

**Finding.** On the full multi-facet set, moving from vanilla to ICOT improves retrieval coverage; **iter=1 and iter=3 look similar** here (same mean hard metrics). Vanilla still leads mean judge overall. Earlier small-n run (`llm_iter_ablation.json`, n=4) had shown larger gains for iter=3 — treat that as preliminary.

### 3.2 Answer-context filtering (multi-facet, n = 12)

Artifact: `answer_context_filter_multifacet.json`. Same ICOT retrieval; generate from full accumulated docs vs filtered (≤6).

| Answer context | Mean judge overall | Wins | Avg docs |
|----------------|--------------------|------|----------|
| Full accumulated | **3.33** | 5 | 20.0 |
| Filtered (≤6) | 3.31 | 4 | 6.0 |

*(3 ties; delta ≈ −0.02.)*

**Finding.** On the full multi-facet set, filtering is **near-neutral** on LLM-judge overall while cutting context ~20→6 docs (efficiency / noise control). The earlier small compare (`answer_context_filter_compare.json`, n=5: filtered 3.80 vs full 2.20) overstated the gain — keep that as a pilot, report **n=12** as primary.

---

## 4. Mixed smoke set (when ICOT helps less)

Artifact: `llm_judge_smoke.json` (n=10 mixed categories; ICOT iter=2 + filter).

| Method | Judge overall | Judge wins |
|--------|---------------|------------|
| Vanilla | **3.08** | **5** |
| Facet ICOT | 2.80 | 2 (3 ties) |

**Finding.** On mixed/single-facet questions, vanilla is often competitive. ICOT’s advantage is **concentrated on multi-facet needs**.

---

## 5. Qualitative observations

- CVE questions benefit from identifier boosting + filtered context when the KB contains the record.  
- Faithfulness questions asking for absent KB facts fail for RAG and prompt-only alike.  
- Prompt-only answers often speculate on CVEs/behaviours without evidence — consistent with low reliability.

---

## 6. Limitations

1. **KB scale.** IoT-23 expanded to 23 scenarios (+ family rollups); VARIoT remains a capped sample; product fields remain incomplete for many vulns.  
2. **Eval scale.** Main three-way uses n=12; some ablations are smaller.  
3. **LLM-as-judge** is noisy; human ratings are future work.  
4. **Generator** is a small free-tier model with truncated evidence.  
5. **ChatIoT-style** baseline is a per-source merge (not a learned selector); true ChatIoT remains a related-work approximation.

---

## 7. Takeaway

Facet-aware ICOT-RAG (multi-source init + needed-facet stop + filtered answering) **beats prompt-only ICoT**, **matches/leads ChatIoT-style on full-set facet/source coverage**, and **wins facet@6 and faithfulness** on the n=50 expanded-KB run. On the multi-facet subset it also leads mean judge overall. Vanilla can still win full-set mean judge — claim **grounded multi-facet completeness + budgeted evidence + trace**, not “always best prose.”

---

### Artifact index

| File | Role |
|------|------|
| `artifacts/evaluation/full_four_way.json` | **Main** full-set 4-way (n=50) |
| `artifacts/evaluation/multifacet_three_way.json` | Earlier 3-way multi-facet (n=12) |
| `artifacts/evaluation/multifacet_vanilla_vs_icot.json` | Earlier pairwise multi-facet run |
| `artifacts/evaluation/llm_iter_ablation_multifacet.json` | Scaled iteration ablation (n=12) |
| `artifacts/evaluation/answer_context_filter_multifacet.json` | Scaled filter ablation (n=12) |
| `artifacts/evaluation/llm_iter_ablation.json` | Earlier iteration ablation (n=4) |
| `artifacts/evaluation/answer_context_filter_compare.json` | Earlier filter pilot (n=5) |
| `artifacts/evaluation/llm_judge_smoke.json` | Mixed smoke judge (n=10) |
| `artifacts/evaluation/prompt_only_icot_smoke.json` | Prompt-only smoke |
