# Submission plan — 30-day journal sprint

> Pivot: **journal-first** (one month). Aligns with `publishability_workflow.md` Phase 4–7, compressed.

## Claim (frozen — do not overclaim)

Facet-aware iterative retrieval improves **multi-source, multi-facet evidence completeness** vs vanilla RAG and clearly beats **prompt-only ICoT**. Against ChatIoT-style multi-retriever, ICOT is competitive on retrieval and strongest on **judge win-count / explainable sufficiency**; answer-quality means are **not** automatic wins.

## Target venue (pick by Day 2)

| Option | Fit | Notes |
|--------|-----|--------|
| **IEEE Access** (recommended) | Applied RAG + IoT security | Faster cycle, broader scope, APC; most realistic in 1 month |
| IEEE Internet of Things Journal | Stronger IoT framing | Higher bar; need thicker KB + human study |
| IEEE TDSC / TIFS | Security systems | Likely needs faithfulness + stronger baselines |

**Default if undecided:** IEEE Access, IEEE journal template.

## Fixed evaluation protocol (unchanged)

| Setting | Value |
|---------|--------|
| Dataset | `datasets/evaluation/iot_security_eval_v1.json` (**50** questions) |
| Primary report | Full set + **multi_facet** subset (12) |
| Methods | Vanilla RAG · Prompt-only ICoT · ChatIoT-style · Facet ICOT |
| Facet ICOT | `max_iterations=3`, answer-context filter **on** |
| Hard metrics | facet recall, source hit, keyword hit (+ **mean ± std**, paired tests) |
| Soft metrics | LLM-as-judge + **human** (faithfulness, usefulness, technical correctness) |
| Journal extras | Automatic faithfulness/citation support; latency/#docs; error analysis |
| Artifacts | `artifacts/evaluation/full_four_way.json` + human + faithfulness |

## Current freeze status

| Item | Status |
|------|--------|
| Protocol locked | Done |
| Full 50-Q four-way | Done (`full_four_way.json`) |
| Scaled ablations (iter + filter, n=12) | Done |
| ChatIoT-style baseline | Done |
| Methods / Results drafts | Seed done |
| Human eval answers | **Partial** (~16/24 in `answers_full.json`) |
| Blind sheets + ratings | **Not started** |
| Intro / Related Work / IEEE `.tex` | **Not started** |
| Faithfulness metric + significance | **Not started** |

---

## 30-day sprint (must ship)

### Week 1 — Close evidence gaps (Days 1–7)

**Goal:** journal-grade numbers, not more prototype features.

| Day | Task | Owner / exit |
|-----|------|----------------|
| 1–2 | Finish human-eval pack: `export_human_eval_pack.py --resume` → 24 answers + sheets | `sheets/*.md` + `ratings_template.csv` |
| 1–2 | Confirm venue + download IEEE journal template | `paper/ieee/` or Overleaf project |
| 2–5 | Collect human ratings (**≥2 raters**, all 24 Q) | `ratings_filled.csv` |
| 3–5 | Add significance: mean±std + paired Wilcoxon/bootstrap on n=50 hard + judge | script + tables in Results |
| 3–6 | Add **faithfulness / citation support** metric over retrieved docs | new artifact + Results subsection |
| 5–7 | Error analysis: multi-facet vs single-facet; when ICOT helps/hurts | 1 table + short prose |
| 6–7 | Optional if quota allows: stronger fixed LLM re-run (same model all methods) | else keep 8B and disclose as limitation |

**Do not start:** UI polish, new demo features, expanding README.

### Week 2 — Journal extras + figures (Days 8–14)

| Day | Task | Exit |
|-----|------|------|
| 8–10 | Latency / doc-count / iteration cost vs quality (from existing traces if possible) | 1 trade-off table/figure |
| 8–11 | Light KB thickening if feasible (extra IoT-23 behaviour notes) — only if it does not block writing | updated index note in Methods |
| 10–12 | Architecture + facet→source + results figures (IEEE-ready) | PNG/PDF figures |
| 11–14 | Expand Methods + Results drafts into camera-ready sections | full Methods/Experiments/Results |

### Week 3 — Full manuscript (Days 15–21)

| Day | Task | Exit |
|-----|------|------|
| 15–17 | Related Work (ICoT, ChatIoT, Self/Adaptive-RAG, security RAG) | section draft |
| 15–18 | Introduction + contributions (match tables; no overclaim) | section draft |
| 18–20 | Discussion, Limitations, Conclusion, Abstract | complete narrative |
| 19–21 | Assemble IEEE LaTeX; cite only frozen artifacts | compiling `.tex` PDF |

### Week 4 — Polish + submit (Days 22–30)

| Day | Task | Exit |
|-----|------|------|
| 22–24 | Internal checklist: every number → JSON artifact; claim ↔ tables | checklist signed-off |
| 24–26 | Proofread; cut fluff; anonymity/ethics if required | clean PDF |
| 26–28 | Reproducibility blurb + code/data availability statement | paragraph in paper |
| 28–30 | Submit + archive submission package | submission ID |

---

## Must-have vs cuttable (if time slips)

**Must-have for a serious journal shot**

1. Human eval analyzed (even 2 raters × 24 Q)
2. Full IEEE manuscript (Abstract→Conclusion) with figures
3. Honest claim matching four-way tables
4. Significance (mean±std + at least one paired test)
5. Faithfulness or citation-grounding metric
6. Clear ChatIoT-style vs ICOT positioning + limitations

**Cut if needed (do not block submit)**

- Stronger LLM full re-run
- Large KB expansion
- Extra baseline beyond current four
- Latency micro-benchmarks beyond what’s in traces
- Public GitHub polish

---

## Commands (human pack)

```bash
# Finish answers + build blind sheets (resume-safe)
python scripts/export_human_eval_pack.py --resume

# Sheets only if answers already complete
python scripts/export_human_eval_pack.py --sheets-only

# After ratings_filled.csv exists
python scripts/analyze_human_ratings.py paper/human_eval/ratings_filled.csv
```

## Weekly checkpoint questions

1. Do human ratings exist?
2. Do Results tables include ±std / significance?
3. Does the PDF compile in IEEE template?
4. Does every claim sentence match a frozen artifact?

If any Week-1 item is red at Day 7, **stop feature work** and finish evidence + writing only.
