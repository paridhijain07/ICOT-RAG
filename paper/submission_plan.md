# Submission plan (locked protocol)

> Living plan for conference-first, then journal. Aligns with `publishability_workflow.md`.

## Claim (frozen)

Facet-aware iterative retrieval improves **multi-source, multi-facet evidence completeness** vs vanilla RAG and clearly beats **prompt-only ICoT**. Answer-quality wins are not automatic.

## Venue

- **Primary:** conference / workshop (IoT security, RAG, or applied AI)
- **Later:** journal extension after human eval + stronger baselines

## Fixed evaluation protocol

| Setting | Value |
|---------|--------|
| Dataset | `datasets/evaluation/iot_security_eval_v1.json` (**50** questions) |
| Primary report | Full set + **multi_facet** subset (12) |
| Methods | Vanilla RAG · Prompt-only ICoT · ChatIoT-style · Facet ICOT |
| Facet ICOT | `max_iterations=3`, answer-context filter **on** |
| Vanilla | `k=5`, unified index |
| ChatIoT-style | `k_per_source=3` from MITRE/VARIoT/IoT23, merge top 8, single generate |
| Prompt-only | Zeng-style 3-stage CoT, no retrieval |
| Hard metrics | facet recall, source hit, keyword hit |
| Soft metrics | LLM-as-judge (reliability, relevance, technicality, friendliness) |
| LLM | Same provider/model for generate + judge (record in artifact `config`) |
| Artifacts | `artifacts/evaluation/full_three_way.json` / `full_four_way.json` |

## Commands

```bash
# Smoke (3 questions)
python scripts/run_full_eval.py --limit 3 --four-way

# Full 50, four-way (resume-safe)
python scripts/run_full_eval.py --four-way --resume

# Multi-facet only
python scripts/run_full_eval.py --category multi_facet --four-way
```

## Immediate backlog

1. ~~Run full four-way eval (50 Q) → freeze JSON~~ **Done**  
2. ~~Update `results_draft.md` from full-set + by-category tables~~ **Done**  
3. Scale filter / iteration ablations on multi-facet (**in progress** — `scripts/run_scaled_ablations.py`)  
4. Human rubric + 20–30 Q ratings — **pack ready** (`paper/human_eval/`); collect ratings next  
5. Write Intro + Related Work  

## Status

| Item | Status |
|------|--------|
| Protocol locked | Done (this file) |
| ChatIoT-style baseline code | Done (`run_chatiot_style`) |
| Resumable full eval script | Done (`scripts/run_full_eval.py`) |
| Full 50-Q numbers | **Done** (`full_four_way.json`, n=50) |
| Human eval | Not started |
| Intro / Related Work | Not started |
