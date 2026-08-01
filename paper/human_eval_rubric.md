# Human evaluation rubric

Blind raters compare answers **without method names**. Use the stratified pack under `paper/human_eval/` (24 questions).

## Setup

1. Build sheets: `python scripts/export_human_eval_pack.py --resume`
2. Give raters `sheets/*.md` + this rubric. **Do not** share `key_DO_NOT_SHARE.json`.
3. Collect scores in a copy of `ratings_template.csv` → `ratings_filled.csv`.

## Scales (integers 1–5)

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| **Faithfulness** | Invents facts / unsupported CVEs or behaviours | Mixed; some unsupported claims | Stays within evidence or clearly marks gaps |
| **Usefulness** | Not actionable for IoT security analysis | Partially useful | Actionable, structured, usable in practice |
| **Technical correctness** | Wrong techniques/CVEs/mitigations | Mixed accuracy | Technically sound given the question/KB |

## Preference (optional)

Rank answers A–D where **1 = best**, **4 = worst**. Ties allowed only if truly indistinguishable (use same rank sparingly).

## Rules for raters

- Score each answer on its own; do not force a winner on every dimension.
- Prefer **faithfulness over fluency** — confident wrong answers score low on faithfulness.
- If gold notes say evidence is missing, reward systems that **admit gaps**.
- Ignore formatting polish unless it hurts clarity.

## Analysis

- Mean ± std per method × dimension  
- Mean preference rank (lower better)  
- Inter-rater agreement when ≥2 raters (Cohen’s κ / Krippendorff’s α — compute externally or extend analyzer)  
- Compare human ranks vs LLM-as-judge from `full_four_way.json`

```bash
python scripts/analyze_human_ratings.py paper/human_eval/ratings_filled.csv
```

## Status

| Item | Status |
|------|--------|
| Rubric | Done |
| Sample + export scripts | Done |
| Full answers + blind sheets | Generating / run export script |
| Ratings collected | Not started |
