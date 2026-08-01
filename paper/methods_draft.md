# Methods (Draft)

> Draft for the ICOT-RAG journal/conference paper. Aligns with implementation under `rag_icot/`.

## 1. Problem setting

We study **open-ended IoT cybersecurity question answering** over a heterogeneous knowledge base that mixes:

- **behavioural** malware/traffic evidence (IoT-23 scenario summaries),
- **adversarial techniques and mitigations** (MITRE ATT&CK),
- **vulnerabilities and exploits** (VARIoT).

A single retrieve-and-generate pass often covers only one evidence type. Prompt-only iterative chain-of-thought (ICoT) can produce fluent advice but is **not grounded** in a curated corpus. Our method, **facet-aware ICOT-RAG**, iteratively retrieves until evidence facets needed by the question are better covered, then answers from a **filtered** evidence subset, while retaining an **explainable reasoning trace**.

---

## 2. Knowledge base construction

### 2.1 Sources

| Source | Role | Index content (approx.) |
|--------|------|-------------------------|
| IoT-23 | Malware / traffic **behaviour** | 9 scenario-level documents (family + labelled behaviours) |
| MITRE ATT&CK | **Technique** / **mitigation** | ~817 IoT/network-filtered techniques |
| VARIoT | **Vulnerability** / **exploit** | ~500 vulns + ~494 exploits |

Documents are normalized, embedded with `BAAI/bge-small-en-v1.5`, and stored in a persistent **Chroma** collection (`icot_knowledge`). Indexed text front-loads identifiers (e.g. CVE, malware family, technique ID) to improve dense retrieval of rare tokens.

### 2.2 Evidence facets

We define five **evidence facets** used for sufficiency checking and retrieval routing:

| Facet | Typical source |
|-------|----------------|
| behaviour | IoT-23 |
| technique | MITRE |
| mitigation | MITRE |
| vulnerability | VARIoT (vuln docs) |
| exploit | VARIoT (exploit docs) |

Facet coverage of a document set is inferred from metadata (`source`, `document_type`).

---

## 3. Proposed method: Facet-aware ICOT-RAG

### 3.1 Overview

Given question \(q\):

1. **Initial retrieval** from the unified index (top-\(k\)).  
2. For up to \(T\) iterations (\(T=3\) by default):  
   - Build a truncated evidence view for the reasoner.  
   - LLM **reasoning step** outputs JSON: thought, confidence, enough_information, covered/missing facets, next_source, next_search_query.  
   - If enough → stop. Else **re-retrieve** with source/facet filters and exclude already-seen IDs.  
3. **Answer-context filtering** selects a compact facet-balanced subset (CVE exact hits prioritized; ≤2 docs/facet; ≤6 total).  
4. **Answer generator** produces a structured IoT security report from the filtered set.  
5. Return answer, full retrieved docs, filtered answer docs, covered facets, and **trace**.

### 3.2 Reasoning step

The reasoner does **not** answer the user. It decides sufficiency across facets and proposes the next retrieval action. Confidence is an LLM self-score in \([0,1]\) (heuristic, not calibrated). The iteration log forms the system’s **process explainability**.

### 3.3 Source-aware re-retrieval

Missing facets map to sources via fixed filters (e.g. behaviour→IoT23, vulnerability→VARIoT vulns). Queries containing CVE IDs also trigger **exact metadata boosts** so rare identifiers are not lost to dense-neighbour noise.

### 3.4 Answer-context filtering

Iterative retrieval can accumulate 15–20 documents. Feeding all of them to the generator reduces reliability. We therefore answer from a filtered subset while keeping the full set for retrieval metrics and auditing.

---

## 4. Baselines

| Name | Retrieval | Reasoning |
|------|-----------|-----------|
| Vanilla RAG | Single pass, \(k=5\), unified index | None |
| Prompt-only ICoT | None | 3-stage role CoT (analyze → expand → advice), Zeng-inspired |
| ChatIoT-style | Per-source retrieve (MITRE / VARIoT / IoT23), merge top docs, single generate | No iteration |
| Facet ICOT-RAG (ours) | Iterative, facet/source filters, \(T=3\) | Sufficiency JSON + filtered answer |

**ChatIoT-style** approximates a single-pass multi-retriever: \(k=3\) from each source, merge/dedupe by distance to at most 8 docs, then one generation. It does **not** include ChatIoT’s learned selector; it is a fair multi-source retrieval baseline without the ICOT loop.

---

## 5. Evaluation protocol

### 5.1 Dataset

`iot_security_eval_v1.json`: 50 questions with category, required facets, expected sources, reference hints, and gold notes. Report **full set (n=50)** and the **multi-facet** subset (12).

### 5.2 Metrics

- **Facet recall / source hit / keyword hit** on retrieved documents.  
- **LLM-as-judge** (same LLM family as generation) on answer quality dimensions.  
- Ablations: `max_iter`, answer-context filter on/off.

### 5.3 Implementation notes

- LLM: Groq `llama-3.1-8b-instant` (temperature low for generation).  
- Evidence prompts are length-truncated to respect API token limits.  
- Pipeline package: `rag_icot` (modular components + `evaluation` runners).  
- Full four-way runner: `scripts/run_full_eval.py --four-way` → `artifacts/evaluation/full_four_way.json`.

---

## 6. Positioning vs prior work

| Work | Retrieval | Iteration | Facet/source routing |
|------|-----------|-----------|----------------------|
| Zeng et al. ICoT | No | Prompt-only CoT | No |
| ChatIoT | Adaptive multi-retriever (single pass) | No iterative re-retrieve | Selector-based |
| **This work** | Unified multi-source RAG | Yes (ICOT loop) | Yes (facet→source) + filtered answering + trace |

---

## 7. Reproducibility

Artifacts under `artifacts/evaluation/` store frozen JSON results. Rebuild scripts live in `scripts/` (KB reindex, smoke, multi-facet three-way). Configuration via project-root `.env` (`LLM_PROVIDER`, API keys).
