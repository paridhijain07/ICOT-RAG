# Results (Draft)

> Working draft for the ICOT-RAG paper. Numbers are from frozen evaluation artifacts under `artifacts/evaluation/`. Generator: Groq `llama-3.1-8b-instant`. Knowledge base: ~1820 documents (MITRE ≈817, VARIoT ≈994, IoT-23 = 9 scenario docs).

## 1. Experimental setup (brief)

We compare three systems on IoT cybersecurity questions:

| Baseline | Description |
|----------|-------------|
| **Vanilla RAG** | Single retrieve → generate over the unified Chroma index |
| **Prompt-only ICoT** | Zeng-style role + multi-stage chain-of-thought advice **with no retrieval** |
| **Facet ICOT-RAG** | Iterative retrieve–reason–retrieve with source/facet routing, `max_iterations=3`, and **answer-context filtering** |

**Hard metrics (retrieval):** facet recall, source hit rate, keyword hit rate.  
**Soft metrics:** LLM-as-judge (1–5) on reliability, relevance, technicality, friendliness (overall = mean).

Prompt-only ICoT has empty retrieval metrics by design (no documents).

---

## 2. Main result: three-way multi-facet comparison

**Setting.** All **12** `multi_facet` questions (≥2 required evidence facets).  
Artifact: `multifacet_three_way.json`.

### Table 1. Mean retrieval and judge scores (n = 12)

| Method | Facet recall ↑ | Source hit ↑ | Keyword hit ↑ | Judge overall ↑ | Judge wins |
|--------|----------------|--------------|---------------|-----------------|------------|
| Vanilla RAG | 0.75 | 0.74 | 0.81 | **3.71** | **6** |
| Prompt-only ICoT (Zeng-style) | 0.00 | 0.00 | 0.00 | 2.15 | 1 |
| Facet ICOT (iter=3, filtered) | **0.88** | **0.89** | **0.83** | 3.35 | 3 |

*(2 ties among methods on judge overall.)*

### Table 2. LLM-as-judge dimensions (n = 12)

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

### 3.1 Iteration budget (multi-facet subset, n = 4)

Artifact: `llm_iter_ablation.json`.

| Condition | Facet recall | Source hit | Keyword hit | Judge overall |
|-----------|--------------|------------|-------------|---------------|
| Vanilla | 0.75 | 0.75 | 0.92 | 3.50 |
| ICOT max_iter=1 | 0.75 | 0.75 | 0.92 | 3.19 |
| **ICOT max_iter=3** | **1.00** | **1.00** | **1.00** | **3.94** |

**Finding.** One iteration is not enough; three iterations restore full facet/source coverage on this subset and yield the best judge score.

### 3.2 Answer-context filtering (controlled compare, n = 5)

Artifact: `answer_context_filter_compare.json`. Same retrieval; generate from full vs filtered context.

| Answer context | Mean judge overall | Wins |
|----------------|--------------------|------|
| Full accumulated docs | 2.20 | 0 |
| **Filtered (≤6 docs)** | **3.80** | **4** (1 tie) |

**Finding.** Unfiltered accumulation hurts reliability. Facet-balanced filtering (+1.6 judge) is part of the proposed pipeline.

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
5. **ChatIoT-style adaptive multi-retriever selector** is not yet a full baseline (single-pass unified index approximates it partially via vanilla RAG).

---

## 7. Takeaway

Facet-aware ICOT-RAG is best framed as improving **multi-source, multi-facet evidence completeness** over vanilla RAG, and as clearly outperforming **prompt-only ICoT**. Answer-quality wins are not automatic; they require filtered generation and remain closest on judge metrics. Position the method as structured retrieval/reasoning over incomplete IoT security KBs—not as a complete KB claim.

---

### Artifact index

| File | Role |
|------|------|
| `artifacts/evaluation/multifacet_three_way.json` | **Main** 3-way multi-facet result (n=12) |
| `artifacts/evaluation/multifacet_vanilla_vs_icot.json` | Earlier pairwise multi-facet run |
| `artifacts/evaluation/llm_iter_ablation.json` | Iteration ablation (n=4) |
| `artifacts/evaluation/answer_context_filter_compare.json` | Context-filter ablation (n=5) |
| `artifacts/evaluation/llm_judge_smoke.json` | Mixed smoke judge (n=10) |
| `artifacts/evaluation/prompt_only_icot_smoke.json` | Prompt-only smoke |
