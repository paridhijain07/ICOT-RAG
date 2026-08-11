# ICOT-RAG

**Facet-aware Iterative Chain-of-Thought RAG for IoT cybersecurity question answering.**

Research prototype that answers open-ended IoT security questions over a mixed knowledge base — malware behaviour (IoT-23), ATT&CK techniques/mitigations (MITRE), and vulnerabilities/exploits (VARIoT) — using iterative retrieve–reason–retrieve with an explainable trace.

> **Status: work in progress.** System, KB, and evaluation harness are usable; paper writing, human study, and some journal extras are still ongoing. Numbers and conclusions in drafts may change.

**Authors:** Paridhi Jain, Pranjali Goyal, Apeksha Jain · Package: `rag_icot` (`0.0.1`)

---

## About the project

### Problem

IoT security questions often need **several kinds of evidence at once** — for example Mirai-like traffic behaviour *and* ATT&CK techniques *and* related CVEs. A normal RAG pipeline does one retrieve → generate pass over a single index and often misses whole evidence types. Prompt-only chain-of-thought (no retrieval) can sound fluent but is **not grounded** in a curated corpus.

### Goal

Build and study a **facet-aware ICOT-RAG** system that:

1. Indexes heterogeneous IoT security sources in one vector store  
2. Uses an LLM **reasoner** (not the final answerer) to check which evidence facets are covered vs missing  
3. **Re-retrieves** from the right source (IoT-23 / MITRE / VARIoT) when something is missing  
4. Answers from a **small filtered** evidence set (to avoid dumping 15–20 noisy docs into the generator)  
5. Exposes a per-iteration **trace** (thought, confidence, facets, next query) for explainability and debugging  

We compare this against vanilla RAG, prompt-only ICoT, and a ChatIoT-style multi-retriever under a shared evaluation protocol. A full **50-Q four-way** automated eval is frozen; **human ratings and the full paper manuscript are still in progress** — see [`paper/`](paper/).

### What you can do with this repo today

- Rebuild / expand the knowledge base from local datasets  
- Run the Streamlit demo (live ICOT + frozen `full_four_way` result tables)  
- Run four-way evaluation and ablations (resume-safe scripts)  
- Export a blind human-rating pack  
- Read methods/results **drafts** (not a finished manuscript)

### Current status (high level)

| Area | Status |
|------|--------|
| Facet ICOT (multi-source init + needed-facet stop) + Streamlit | Working / demo updated |
| Multi-source KB (MITRE + VARIoT + expanded IoT-23) | Working (~1,837 docs) |
| Full 50-Q four-way eval | **Done** — `artifacts/evaluation/full_four_way.json` |
| Ablations (iterations, answer-context filter) | Done (scaled multi-facet) |
| Faithfulness + facet@budget metrics | Done (in four-way summary) |
| Human evaluation (blind sheets) | Pack ready (24/24); **ratings not collected** |
| Paper (Intro / Related Work / IEEE PDF) | **Drafting** |
| Significance tests (mean±std / paired) | Still open |

Working notes: [`paper/submission_plan.md`](paper/submission_plan.md), [`paper/publishability_workflow.md`](paper/publishability_workflow.md), [`paper/results_draft.md`](paper/results_draft.md).

---

## How the system works

### Evidence facets

Questions are treated as needing one or more of:

| Facet | Typical source |
|-------|----------------|
| `behaviour` | IoT-23 scenario / family docs |
| `technique` | MITRE ATT&CK |
| `mitigation` | MITRE ATT&CK |
| `vulnerability` | VARIoT vulnerability docs |
| `exploit` | VARIoT exploit docs |

Facet coverage is inferred from document metadata (`source`, `document_type`).

### Pipeline steps

1. **Infer needed facets** for the question (or use eval-provided facets)  
2. **Multi-source initial retrieve** from IoT-23 / MITRE / VARIoT (merge to a bounded set)  
3. **ICOT loop** (default up to 3 iterations):  
   - If all needed facets are already covered → **stop**  
   - Else reasoner proposes one targeted re-retrieve for a missing needed facet only  
4. **Answer-context filtering** — facet-balanced subset (default ≤2 docs/facet, ≤6 total; CVE hits prioritized)  
5. **Answer generation** — structured IoT security-style report from the filtered set  
6. Return answer + full retrieved docs + filtered docs + covered facets + **trace**

Core entrypoint: `rag_icot.pipeline.rag_icot_pipeline.RAGICOTPipeline`.

```text
Question
   │
   ▼
Infer needed evidence facets
   │
   ▼
Multi-source first retrieve (IoT-23 · MITRE · VARIoT)
   │
   ▼
┌─────────────────────────────────────────────┐
│  ICOT loop (≤ T iterations)                 │
│  • Needed facets covered? → stop            │
│  • Else targeted re-retrieve for missing    │
└─────────────────────────────────────────────┘
   │
   ▼
Answer-context filter (facet-balanced, CVE boost)
   │
   ▼
Generator → grounded IoT security report
   + full docs + filtered docs + covered facets + trace
```

### Main components (`rag_icot/`)

| Area | Responsibility |
|------|----------------|
| `components/` | Data ingestion, KB builders, embeddings, vector store, reasoning engine, answer generator, context filter |
| `constants/` | Facet names and source filters |
| `evaluation/` | Baselines (vanilla, prompt-only, ChatIoT-style, facet ICOT), metrics |
| `pipeline/` | End-to-end `RAGICOTPipeline` |
| `prompts/` | Prompt templates for reasoner / generator / judge |

### Features at a glance

| Feature | Description |
|---------|-------------|
| Unified IoT security KB | MITRE · VARIoT · IoT-23 in one index |
| Facet-aware ICOT loop | Retrieve → sufficiency reason → targeted re-retrieve |
| Answer-context filtering | Compact evidence for generation |
| Baselines + eval scripts | Four-way compare, ablations, LLM-as-judge |
| Human-eval pack | Blind A–D sheets + rubric |
| Streamlit demo | Overview, live run, results, how-it-works |

---

## Repository layout

```text
ICOT-RAG/
├── rag_icot/                 # Installable package
│   ├── components/           # ingestion, KB builders, retrieval, reasoning, generation
│   ├── constants/            # evidence facets, source filters
│   ├── evaluation/           # baselines, metrics, ablation helpers
│   ├── pipeline/             # RAGICOTPipeline
│   └── prompts/
├── scripts/                  # Rebuild KB, eval runners, human-eval export
├── streamlit_app.py          # Interactive demo
├── datasets/                 # Local data (gitignored) — IoT-23, MITRE, eval JSON
├── artifacts/                # Local outputs (gitignored) — Chroma, JSON KBs, eval runs
├── paper/                    # Methods/results drafts, human-eval pack, submission plan
├── notebooks/
├── .env.example
├── requirements.txt
└── setup.py
```

**Note:** `datasets/` and `artifacts/` are gitignored (large / local). You need the raw sources + a rebuilt index on your machine to run live retrieval.

---

## Requirements

- Python 3.10+ recommended  
- API key for an LLM provider (**Groq** recommended for free-tier evals; Gemini optional)  
- Disk space for IoT-23 labeled logs (some captures are multi‑GB)  
- Embedding model download on first run (`BAAI/bge-small-en-v1.5` via `sentence-transformers`)

---

## Setup

```bash
# Clone and enter
cd ICOT-RAG

# Virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt
pip install -e .

# Configure LLM
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS
```

Edit `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

See [`.env.example`](.env.example) for Gemini fallback options.

---

## Knowledge base

### Sources (typical master index)

| Source | Role | Approx. size (current build) |
|--------|------|------------------------------|
| MITRE ATT&CK | Technique / mitigation | ~817 IoT/network-filtered docs |
| VARIoT | Vulnerability / exploit | ~500 + ~494 (capped sample) |
| IoT-23 | Malware / traffic **behaviour** | 23 scenario docs + family rollups |

Master Chroma collection: `artifacts/chroma_db` → collection `icot_knowledge` (**~1,837** documents after IoT-23 expansion).

### Rebuild IoT-23 (after adding scenarios)

Place scenario folders under `datasets/iot23/` with `bro/conn.log.labeled` (nested honeypot paths are supported).

```bash
# Resume-safe aggregates → artifacts/iot23_knowledge.json
python scripts/rebuild_iot23_kb.py

# Merge MITRE + VARIoT + IoT-23, embed, rebuild Chroma
python scripts/rebuild_master_index.py
```

Other builders:

| Script | Purpose |
|--------|---------|
| `scripts/rebuild_variot_kb.py` | Rebuild VARIoT knowledge JSON |
| `scripts/expand_variot_and_reindex.py` | Expand VARIoT sample + reindex |
| `scripts/diagnose_kb_retrieval.py` | Debug retrieval for a query |

IoT-23 notes: [`rag_icot/docs/iot23_notes.md`](rag_icot/docs/iot23_notes.md).

---

## Streamlit demo

```bash
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

| Page | Content |
|------|---------|
| Overview | Project pitch, live KB document count |
| Live demo | Run facet ICOT; answer + filtered docs + trace |
| Results | Frozen tables from `artifacts/evaluation/*.json` |
| How it works | Pipeline overview |

Details: [`paper/demo_streamlit.md`](paper/demo_streamlit.md).

**Live demo** needs `.env` + `artifacts/chroma_db`. **Results** can be browsed offline from frozen JSON artifacts.

---

## Programmatic usage

```python
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

pipeline = RAGICOTPipeline()
result = pipeline.run(
    "What network behaviours does Mirai show in IoT-23?",
    max_iterations=3,
    required_facets=["behaviour", "technique"],
    filter_answer_context=True,
)

print(result["answer"])
print(result["covered_facets"])
print(result["trace"])
```

---

## Evaluation

Primary frozen run: `artifacts/evaluation/full_four_way.json` (n=50, improved Facet ICOT, expanded KB). Tables: [`paper/results_draft.md`](paper/results_draft.md). Human study and significance tests are still open.

### Dataset

`datasets/evaluation/iot_security_eval_v1.json` — **50** IoT cybersecurity questions with categories, required facets, expected sources, and gold notes.

Typical reporting splits:

- Full set (`n=50`)
- Multi-facet subset (`n=12`)

### Methods compared

| Method | Retrieval | Reasoning |
|--------|-----------|-----------|
| Vanilla RAG | Single pass, `k=5`, unified index | None |
| Prompt-only ICoT | None | 3-stage role CoT (Zeng-inspired) |
| ChatIoT-style | Per-source retrieve + merge (no iteration) | None |
| Facet ICOT | Multi-source init → needed-facet stop / refine, `T=3` | Sufficiency JSON + filtered answer |

### Metrics

- **Hard:** facet recall, facet recall@budget (≤6), source hit, keyword hit, faithfulness (ID grounding)  
- **Soft:** LLM-as-judge (reliability, relevance, technicality, friendliness)  
- **Ablations:** `max_iterations`, answer-context filter on/off  
- **Still open:** human ratings, significance tests (mean±std / paired)  

### Run evals

```bash
# Smoke (3 questions, four-way)
python scripts/run_full_eval.py --limit 3 --four-way

# Full 50-Q four-way (resume-safe)
python scripts/run_full_eval.py --four-way --resume

# Multi-facet only
python scripts/run_full_eval.py --category multi_facet --four-way

# Scaled ablations (iterations / filter)
python scripts/run_scaled_ablations.py
```

---

## Human evaluation

Blind pack under [`paper/human_eval/`](paper/human_eval/):

```bash
# Generate answers + blind sheets (resume-safe)
python scripts/export_human_eval_pack.py --resume

# After raters fill ratings_filled.csv
python scripts/analyze_human_ratings.py paper/human_eval/ratings_filled.csv
```

- Rubric: [`paper/human_eval_rubric.md`](paper/human_eval_rubric.md)  
- Give raters only `sheets/*.md` + the rubric  
- **Do not share** `key_DO_NOT_SHARE.json` or `answers_full.json` with raters (both gitignored)

---

## Paper materials (drafts)

These are **working notes**, not a finished submission:

| Path | Role |
|------|------|
| [`paper/methods_draft.md`](paper/methods_draft.md) | Methods draft |
| [`paper/results_draft.md`](paper/results_draft.md) | Results draft from eval artifacts |
| [`paper/submission_plan.md`](paper/submission_plan.md) | Eval protocol + publication checklist |
| [`paper/publishability_workflow.md`](paper/publishability_workflow.md) | Roadmap toward a journal-ready paper |

---

## Configuration reference

| Variable | Meaning |
|----------|---------|
| `LLM_PROVIDER` | `groq` or `gemini` |
| `GROQ_API_KEY` / `GROQ_MODEL` | Groq auth + model |
| `GOOGLE_API_KEY` / `GEMINI_MODEL` | Gemini fallback |

Embedding model (code default): `BAAI/bge-small-en-v1.5` · Vector store: Chroma persistent under `artifacts/chroma_db`.

---

## Limitations

- IoT-23 documents are **scenario-level aggregates**, not full PCAP dumps (no default-password dictionaries in-KB unless added).  
- VARIoT is a **capped sample**; product metadata is incomplete for many vulns.  
- Reasoner **confidence** is an LLM self-score (not calibrated).  
- LLM-as-judge is noisy; human ratings should validate soft metrics.  
- ChatIoT-style baseline is a fair multi-source merge, **not** the full learned ChatIoT selector.  
- Free-tier models may rate-limit during full 50-Q / human-pack runs (scripts support resume + backoff).

---

## Related ideas (how this project differs)

Rough positioning while the Related Work section is still being written:

| Approach | Retrieval | Iteration | Facet / source routing |
|----------|-----------|-----------|------------------------|
| Prompt-only ICoT (e.g. Zeng-style) | No | Prompt CoT only | No |
| ChatIoT-style multi-retriever | Multi-source, single pass | No iterative re-retrieve | Selector / per-source merge |
| This project (ICOT-RAG) | Unified multi-source RAG | Yes (ICOT loop) | Facet→source + filtered answering + trace |

---

## License / data attribution

- **IoT-23:** Aposemat / Stratosphere Lab IoT-23 dataset (respect their license and citation requirements).  
- **MITRE ATT&CK:** © MITRE — follow [ATT&CK terms](https://attack.mitre.org/).  
- **VARIoT:** Use according to the VARIoT project’s terms for vulnerability/exploit data.

This repository’s code is a research prototype; add an explicit license file if you open-source the software itself.

---

## Quick checklist (new machine)

1. `pip install -r requirements.txt && pip install -e .`  
2. Copy `.env.example` → `.env` and set `GROQ_API_KEY`  
3. Ensure `datasets/` sources exist; run `rebuild_iot23_kb.py` + `rebuild_master_index.py` if Chroma is missing  
4. `streamlit run streamlit_app.py`  
5. Optional: `python scripts/run_full_eval.py --limit 3 --four-way`
