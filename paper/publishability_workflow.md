# Journal publishability workflow

Roadmap to turn ICOT-RAG from a working research prototype into a submission-ready paper.  
**Target path:** strengthen evidence → conference/workshop first → then journal.

Current status (honest):

- Done: improved facet ICOT (multi-source init + needed-facet stop), KB (~1837 docs), Streamlit (Results from `full_four_way.json`), protocol, ChatIoT-style baseline, **full 50-Q four-way** (n=50, 0 errors), Methods/Results drafts, faithfulness + facet@budget in eval, human-eval pack (24 sheets).
- In progress: human **ratings** collection; Intro / Related Work / IEEE manuscript.
- Not done: significance tests, conference/journal PDF packaging.

---

## Guiding claim (do not drift)

Lead claim:

> Facet-aware iterative retrieval improves **multi-source, multi-facet evidence completeness** vs vanilla RAG and clearly beats **prompt-only ICoT**.

Do **not** claim “always better answers” — vanilla often wins LLM-judge scores on the current set.

---

## Phase overview

| Phase | Goal | Exit criteria |
|-------|------|----------------|
| **0. Lock scope** | Venue + claim + baselines | Written 1-page plan |
| **1. Strengthen system** | Fair, reproducible pipeline | Same LLM/settings for all methods |
| **2. Full evaluation** | n=50 + ablations | Frozen JSONs + tables |
| **3. Strong baselines** | ChatIoT-style included | 4-way comparison table |
| **4. Human study** | Validate judge | Agreement report |
| **5. Write paper** | Full manuscript | Intro→Conclusion draft |
| **6. Conference submit** | Get reviews | Submitted PDF |
| **7. Journal stretch** | Extra rigor | Human + faithfulness + richer KB |

Work **Phases 1–5 in order**. Skip ahead only if blocked (e.g. waiting on raters while writing Related Work).

---

## Phase 0 — Lock scope (1–2 days)

**Workflow**

1. Pick venue type: workshop / conference first (recommended), journal later.
2. Write a one-page plan: problem, novelty, 3 baselines, metrics, claim sentence.
3. Freeze eval protocol: which questions, which model, seeds, max iterations.

**Deliverable:** `paper/submission_plan.md` (venue, deadline, claim, baselines list).

---

## Phase 1 — Strengthen system for fair comparison (3–7 days)

**Workflow**

1. Fix one **generator LLM** for all methods (prefer stronger than free-tier 8B if quota allows).
2. Pin versions: embedding model, Chroma collection, prompt templates, temperature.
3. Ensure every baseline uses the **same KB** and logging format (answer, docs, trace/metrics).
4. Document config in `.env.example` + a short `paper/reproducibility.md`.

**Deliverables**

- Single config used by vanilla / prompt-only / facet ICOT / (later) ChatIoT-style.
- Reproducible run scripts under `scripts/`.

---

## Phase 2 — Full evaluation (1–2 weeks)

**Workflow**

1. Run **three-way** (vanilla · prompt-only ICoT · facet ICOT) on **all 50** questions.
2. Split reporting:
   - multi-facet subset
   - single-facet / mixed
3. Re-run ablations at proper scale:
   - iteration budget (`max_iter` 1 vs 3)
   - answer-context filter on vs off
4. Save frozen artifacts under `artifacts/evaluation/`.
5. Update `paper/results_draft.md` tables from those JSONs only (no hand-wavy numbers).

**Scripts to extend / reuse**

- `scripts/run_multifacet_three_way.py` → generalize to full set
- `scripts/run_judge_and_iter_ablation.py`
- `scripts/compare_answer_context_filter.py`

**Exit criteria**

- Full-set tables + multi-facet subset tables
- Means (ideally ± std) for hard metrics + judge

---

## Phase 3 — Strong baselines (1–2 weeks)

**Workflow**

1. Implement **ChatIoT-style** baseline (or closest fair variant):
   - single-pass multi-retriever / source selector
   - **no** iterative re-retrieve
2. Put it in `rag_icot/evaluation/baselines.py` and a run script.
3. Run **four-way** comparison on the same 50 questions.
4. Optional fifth baseline only if needed by venue (e.g. BM25-only, or plain CoT+RAG without facets).

**Exit criteria**

- Table: Vanilla | Prompt-only ICoT | ChatIoT-style | Facet ICOT  
- Clear text: what ChatIoT-style is and how it differs from yours

---

## Phase 4 — Human evaluation (2–3 weeks, can overlap writing)

**Workflow**

1. Sample **20–30** questions (stratify multi-facet vs others).
2. Blind raters to method name; show question + answers (shuffled).
3. Rate (1–5): faithfulness, usefulness, technical correctness (define rubric in 1 page).
4. Compute mean scores + inter-rater agreement (e.g. Cohen’s κ / Krippendorff’s α).
5. Compare human ranks vs LLM-judge (does judge track humans?).

**Deliverables**

- `paper/human_eval_rubric.md`
- Spreadsheet / JSON of ratings
- Short subsection in Results

---

## Phase 5 — Write the full paper (2–3 weeks)

**Section workflow**

| Order | Section | Source |
|-------|---------|--------|
| 1 | Methods | Expand `paper/methods_draft.md` |
| 2 | Experiments / Results | Expand `paper/results_draft.md` |
| 3 | Related Work | New — Zeng ICoT, ChatIoT, RAG-for-security, iterative RAG |
| 4 | Introduction | New — problem → gap → claim → contributions |
| 5 | Discussion + Limitations | Honest: KB thin spots, n, judge noise |
| 6 | Conclusion | Contributions + future work |
| 7 | Abstract + figures | Architecture diagram, pipeline, main table |

**Figures to produce**

1. System architecture (KB → retrieve → ICOT loop → filter → answer + trace)  
2. Facet → source mapping  
3. Main results bar chart / table  
4. Ablation (iterations, filter)

**Exit criteria:** complete draft PDF in venue template.

---

## Phase 6 — Conference / workshop submission

**Workflow**

1. Format to venue template (page limit, refs, anonymity if needed).
2. Internal checklist: claim matches tables; all numbers trace to artifacts.
3. Proofread; cut overclaims.
4. Submit; keep rebuttal notes ready.

**After reviews:** revise → either camera-ready or plan journal extension.

---

## Phase 7 — Journal extension (after conference or in parallel if strong)

Only after Phase 2–4 are solid.

**Extra work journals often want**

1. Richer KB (more IoT-23 behaviour docs; cleaner VARIoT metadata).  
2. **Faithfulness / citation support** metrics (answer grounded in retrieved docs).  
3. Larger human study.  
4. Latency / cost vs accuracy.  
5. Error analysis: when ICOT helps vs hurts.  
6. Optional: calibrated confidence (current confidence is LLM self-score).  
7. Public code + data release statement.

---

## Priority backlog (do in this order)

1. Full **50-Q** three-way eval + update Results tables  
2. **ChatIoT-style** baseline + four-way table  
3. Scale ablations (filter + iterations) to multi-facet / full set  
4. Human rating rubric + 20–30 Q study  
5. Write Intro + Related Work  
6. Architecture figure + clean camera-ready draft  
7. KB expansion + faithfulness metrics (journal)

---

## What not to do yet

- Expanding README for GitHub (optional, not blocking science).  
- Polishing Streamlit UI beyond demo needs.  
- Claiming journal-readiness before n=50 + strong baseline + human subset.  
- Changing the core claim to “best chatbot answers.”

---

## Weekly checklist template

Copy per week:

```text
Week of: ____
Focus phase: ____

[ ] Experiments run / artifacts saved
[ ] Tables updated in paper/results_draft.md
[ ] Code/scripts committed
[ ] Writing progress (section: ____)
[ ] Blockers: ____
[ ] Next week: ____
```

---

## Artifact map (keep frozen)

| Artifact | Role |
|----------|------|
| `artifacts/evaluation/multifacet_three_way.json` | Current main 3-way (n=12) — replace/extend with full-set run |
| `artifacts/evaluation/llm_iter_ablation.json` | Iteration ablation — re-run larger |
| `artifacts/evaluation/answer_context_filter_compare.json` | Filter ablation — re-run larger |
| `paper/methods_draft.md` | Methods seed |
| `paper/results_draft.md` | Results seed |
| `streamlit_app.py` | Demo only (not a paper contribution) |

---

## Suggested timeline (aggressive)

| Weeks | Focus |
|-------|--------|
| 1 | Phase 0–1 lock + stronger fixed LLM |
| 2–3 | Phase 2 full 50-Q + ablations |
| 4–5 | Phase 3 ChatIoT-style baseline |
| 5–7 | Phase 4 human eval (overlap with writing) |
| 6–8 | Phase 5 full paper draft |
| 9 | Phase 6 submit conference |

Journal = add **4–8+ weeks** after that for Phase 7.
