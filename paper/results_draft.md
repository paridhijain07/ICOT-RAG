# Results (Draft)

> Working draft for the ICOT-RAG paper. Numbers are from frozen evaluation artifacts under `artifacts/evaluation/`. Generator: Groq `llama-3.1-8b-instant`. Knowledge base: ~1820 documents (MITRE ≈817, VARIoT ≈994, IoT-23 = 9 scenario docs).

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
| **Facet ICOT-RAG** | Iterative retrieve–reason–retrieve with source/facet routing, `max_iterations=3`, and **answer-context filtering** |

**Hard metrics (retrieval):** facet recall, source hit rate, keyword hit rate.  
**Soft metrics:** LLM-as-judge (1–5) on reliability, relevance, technicality, friendliness (overall = mean).

Prompt-only ICoT has empty retrieval metrics by design (no documents).

---

## 2. Main result: full-set four-way comparison (n = 50)

Artifact: `full_four_way.json`. Generator: Groq `llama-3.1-8b-instant`.

### Table 1. Mean retrieval and judge scores (full set)

| Method | Facet recall ↑ | Source hit ↑ | Keyword hit ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|--------------|---------------|-----------------|------------|
| Vanilla RAG | 0.86 | 0.87 | 0.82 | **3.17** | 11 |
| Prompt-only ICoT | 0.00 | 0.00 | 0.00 | 1.74 | 4 |
| ChatIoT-style | **0.97** | **1.00** | **0.89** | 3.01 | 8 |
| Facet ICOT | 0.92 | 0.92 | 0.86 | 3.13 | **12** |

*(15 judge ties.)*

### Finding (full set)

1. **Prompt-only ICoT fails** without retrieval (lowest judge; zero hard metrics).  
2. **ChatIoT-style leads retrieval coverage** (facet / source / keyword) via per-source retrieve+merge.  
3. **Facet ICOT is competitive** on retrieval and has the **most judge wins**, while vanilla edges mean judge overall.  
4. Iteration alone is not enough to beat a strong multi-source single pass on every metric — position ICOT as **structured sufficiency + explainable trace**, not automatic judge dominance.

---

## 2b. Multi-facet subset (n = 12)

Same artifact; category `multi_facet` (≥2 required evidence facets).

### Table 2. Multi-facet four-way

| Method | Facet recall ↑ | Source hit ↑ | Keyword hit ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|--------------|---------------|-----------------|------------|
| Vanilla RAG | 0.75 | 0.74 | 0.81 | **3.46** | 2 |
| Prompt-only ICoT | 0.00 | 0.00 | 0.00 | 2.00 | 2 |
| ChatIoT-style | **1.00** | **1.00** | **0.94** | 3.42 | 2 |
| Facet ICOT | 0.88 | 0.89 | 0.83 | 3.23 | **3** |

*(3 ties.)*

### Finding (multi-facet)

On questions that need multiple evidence types, **ChatIoT-style achieves perfect facet/source coverage** in this run. Facet ICOT improves over vanilla on retrieval (facet +0.13, source +0.15) but trails the multi-retriever single pass. Earlier three-way artifact (`multifacet_three_way.json`) without ChatIoT-style remains useful for the Zeng-style contrast.

---

## 2c. Earlier three-way multi-facet (reference)

**Setting.** Same **12** multi-facet questions; vanilla vs prompt-only vs facet ICOT only.  
Artifact: `multifacet_three_way.json`.

### Table 3. Mean retrieval and judge scores (n = 12, three-way)

| Method | Facet recall ↑ | Source hit ↑ | Keyword hit ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|--------------|---------------|-----------------|------------|
| Vanilla RAG | 0.75 | 0.74 | 0.81 | **3.71** | **6** |
| Prompt-only ICoT (Zeng-style) | 0.00 | 0.00 | 0.00 | 2.15 | 1 |
| Facet ICOT (iter=3, filtered) | **0.88** | **0.89** | **0.83** | 3.35 | 3 |

*(2 ties among methods on judge overall.)*

### Table 4. LLM-as-judge dimensions (n = 12, three-way)

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

1. **KB scale.** IoT-23 has nine scenario docs; VARIoT is a capped sample; product fields remain incomplete for many vulns.  
2. **Eval scale.** Main three-way uses n=12; some ablations are smaller.  
3. **LLM-as-judge** is noisy; human ratings are future work.  
4. **Generator** is a small free-tier model with truncated evidence.  
5. **ChatIoT-style** baseline is a per-source merge (not a learned selector); true ChatIoT remains a related-work approximation.

---

## 7. Takeaway

Facet-aware ICOT-RAG clearly beats **prompt-only ICoT** and improves multi-facet coverage vs **vanilla** single-pass retrieval. Against a **ChatIoT-style multi-retriever**, ICOT does not win raw facet/source hit rates in the n=50 run — the multi-source merge is a strong baseline. ICOT’s differentiators for the paper are **iterative sufficiency checking**, **answer-context filtering**, and an **explainable trace**. Answer-quality (judge) wins are mixed; do not overclaim “always better answers.”

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
