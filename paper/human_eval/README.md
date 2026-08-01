# Human evaluation pack

Blind ratings of four systems on a **stratified 24-question** sample from `iot_security_eval_v1.json`.

## Systems (hidden from raters)

| Code in key | Method |
|-------------|--------|
| `vanilla` | Vanilla RAG |
| `prompt_only_icot` | Prompt-only ICoT |
| `chatiot_style` | ChatIoT-style multi-retriever |
| `facet_icot` | Facet ICOT-RAG |

On each sheet, answers are shuffled as **A / B / C / D**. Mapping is only in `key_DO_NOT_SHARE.json` — do not give that file to raters.

## Files

| Path | Purpose |
|------|---------|
| `sample.json` | Sampled question IDs + strata |
| `answers_full.json` | Full regenerated answers (after export script) |
| `sheets/*.md` | Blind rating sheets for raters |
| `ratings_template.csv` | Empty score grid to fill |
| `key_DO_NOT_SHARE.json` | Label → method (organizer only) |
| `../human_eval_rubric.md` | Scoring rubric |

## Build / regenerate

```bash
# Generate answers + sheets (resume-safe; uses Groq quota)
python scripts/export_human_eval_pack.py --resume

# If answers already exist, only rebuild sheets
python scripts/export_human_eval_pack.py --sheets-only
```

## Rater instructions (short)

1. Read the question and optional gold notes.
2. Score **each** of A–D independently (1–5): Faithfulness, Usefulness, Technical correctness.
3. Optionally rank A–D (1 = best).
4. Enter scores in `ratings_template.csv` (copy to `ratings_filled.csv`), one row per (rater, question, label).
5. Use a stable `rater_id` (e.g. `r1`, `r2`).

Target: **2–3 raters**, all 24 sheets if possible (or split 12/12).

## After ratings

```bash
python scripts/analyze_human_ratings.py paper/human_eval/ratings_filled.csv
```

Writes `artifacts/evaluation/human_eval_summary.json`.
