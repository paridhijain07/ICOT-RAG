"""Build a blind human-evaluation pack from the 50-Q four-way artifact.

1. Stratified sample of questions (default 24)
2. Regenerate full answers for four methods (resume-safe)
3. Write blind sheets (methods shuffled as A/B/C/D) + rating CSV + secret key

Examples:
  python scripts/export_human_eval_pack.py --limit 24
  python scripts/export_human_eval_pack.py --resume
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.evaluation import (
    load_eval_dataset,
    run_chatiot_style,
    run_facet_icot,
    run_prompt_only_icot,
    run_vanilla_rag,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

METHODS = ["vanilla", "prompt_only_icot", "chatiot_style", "facet_icot"]
OUT_DIR = root / "paper" / "human_eval"
ANSWERS_PATH = OUT_DIR / "answers_full.json"
SAMPLE_PATH = OUT_DIR / "sample.json"
KEY_PATH = OUT_DIR / "key_DO_NOT_SHARE.json"
RATINGS_CSV = OUT_DIR / "ratings_template.csv"
SHEETS_DIR = OUT_DIR / "sheets"
SEED = 42

# Target counts per category (sum = 24)
STRATA = {
    "multi_facet": 8,
    "behaviour": 4,
    "vulnerability": 4,
    "technique": 3,
    "faithfulness": 3,
    "mitigation": 1,
    "exploit": 1,
}


def _is_rate_limit(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "ratelimit" in type(exc).__name__.lower()
        or "rate limit" in msg
        or "429" in msg
        or "tokens per day" in msg
    )


def _rate_limit_sleep_seconds(exc: BaseException, fallback: float = 180.0) -> float:
    m = re.search(
        r"try again in\s+(?:(\d+)m)?\s*([\d.]+)s",
        str(exc),
        flags=re.IGNORECASE,
    )
    if not m:
        return fallback
    return max(fallback, int(m.group(1) or 0) * 60 + float(m.group(2) or 0) + 5)


def stratified_sample(questions: list, limit: int, seed: int) -> list:
    rng = random.Random(seed)
    by_cat: dict[str, list] = {}
    for q in questions:
        by_cat.setdefault(q.category, []).append(q)
    for cat in by_cat:
        rng.shuffle(by_cat[cat])

    picked = []
    for cat, n in STRATA.items():
        pool = by_cat.get(cat, [])
        take = min(n, len(pool))
        picked.extend(pool[:take])

    # Fill if under limit
    leftover = [q for q in questions if q not in picked]
    rng.shuffle(leftover)
    while len(picked) < limit and leftover:
        picked.append(leftover.pop())
    return picked[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pause", type=float, default=5.0)
    parser.add_argument("--max-retries", type=int, default=8)
    parser.add_argument(
        "--answers-only",
        action="store_true",
        help="Only generate answers; skip sheet export",
    )
    parser.add_argument(
        "--sheets-only",
        action="store_true",
        help="Export sheets from existing answers_full.json",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)

    questions = load_eval_dataset(
        root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
    )
    sample = stratified_sample(questions, args.limit, SEED)
    SAMPLE_PATH.write_text(
        json.dumps(
            {
                "seed": SEED,
                "n": len(sample),
                "strata": STRATA,
                "ids": [q.id for q in sample],
                "by_category": {
                    cat: [q.id for q in sample if q.category == cat]
                    for cat in sorted({q.category for q in sample})
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Sample {len(sample)} ids -> {SAMPLE_PATH}", flush=True)

    answers: dict[str, dict] = {}
    if ANSWERS_PATH.exists():
        answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")).get(
            "answers", {}
        )

    if not args.sheets_only:
        print("Loading pipeline...", flush=True)
        pipeline = RAGICOTPipeline()
        retriever = pipeline.engine.retriever
        generator = pipeline.generator
        print(
            "LLM",
            generator.llm.provider,
            generator.llm.model_name,
            flush=True,
        )

        for q in sample:
            row = answers.get(q.id, {"id": q.id, "methods": {}})
            row["id"] = q.id
            row["category"] = q.category
            row["question"] = q.question
            row["gold_notes"] = q.gold_notes
            row["required_facets"] = q.required_facets
            row.setdefault("methods", {})

            missing = [m for m in METHODS if m not in row["methods"]]
            if args.resume and not missing:
                print(f"Skip {q.id} (complete)", flush=True)
                answers[q.id] = row
                continue

            print("\n" + "=" * 80, flush=True)
            print(q.id, q.category, missing or METHODS, flush=True)

            for method in missing or []:
                attempt = 0
                while True:
                    attempt += 1
                    try:
                        if method == "vanilla":
                            run = run_vanilla_rag(
                                q.question,
                                k=5,
                                retriever=retriever,
                                generator=generator,
                            )
                        elif method == "prompt_only_icot":
                            run = run_prompt_only_icot(
                                q.question, llm=generator.llm
                            )
                        elif method == "chatiot_style":
                            run = run_chatiot_style(
                                q.question,
                                k_per_source=3,
                                max_docs=8,
                                retriever=retriever,
                                generator=generator,
                            )
                        else:
                            run = run_facet_icot(
                                q.question,
                                max_iterations=3,
                                pipeline=pipeline,
                                required_facets=q.required_facets,
                                filter_answer_context=True,
                            )
                        row["methods"][method] = {
                            "answer": run.get("answer") or "",
                            "covered_facets": run.get("covered_facets") or [],
                        }
                        print(
                            f"  {method}: {len(row['methods'][method]['answer'])} chars",
                            flush=True,
                        )
                        time.sleep(1.5)
                        break
                    except Exception as exc:
                        if _is_rate_limit(exc) and attempt <= args.max_retries:
                            wait = _rate_limit_sleep_seconds(exc)
                            print(
                                f"RATE LIMIT {q.id}/{method} "
                                f"{attempt}/{args.max_retries}; sleep {wait:.0f}s",
                                flush=True,
                            )
                            time.sleep(wait)
                            continue
                        print(
                            f"FAILED {q.id}/{method}: {type(exc).__name__}: {exc}",
                            flush=True,
                        )
                        row["methods"][method] = {
                            "answer": "",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                        break

            answers[q.id] = row
            ANSWERS_PATH.write_text(
                json.dumps(
                    {
                        "config": {
                            "methods": METHODS,
                            "seed": SEED,
                            "n": len(sample),
                            "llm_provider": generator.llm.provider,
                            "llm_model": generator.llm.model_name,
                        },
                        "answers": answers,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            time.sleep(args.pause)

        if args.answers_only:
            print("Answers saved; skipping sheets.", flush=True)
            return

    # --- Export blind sheets + key + CSV template ---
    if not ANSWERS_PATH.exists():
        raise SystemExit("No answers_full.json — run without --sheets-only first")

    blob = json.loads(ANSWERS_PATH.read_text(encoding="utf-8"))
    answers = blob["answers"]
    rng = random.Random(SEED)
    key = {"seed": SEED, "items": {}}

    rating_rows = []
    for qid in [q.id for q in sample]:
        item = answers.get(qid)
        if not item or len(item.get("methods") or {}) < 4:
            print(f"Incomplete answers for {qid}; skip sheet", flush=True)
            continue
        labels = ["A", "B", "C", "D"]
        order = METHODS[:]
        rng.shuffle(order)
        mapping = {lab: meth for lab, meth in zip(labels, order)}
        key["items"][qid] = mapping

        lines = [
            f"# Human eval sheet — {qid}",
            "",
            f"**Category:** {item.get('category')}",
            "",
            "## Question",
            item["question"],
            "",
            "## Gold notes (optional reference)",
            item.get("gold_notes") or "_(none)_",
            "",
            "Rate each answer 1–5 on Faithfulness, Usefulness, Technical correctness.",
            "Do not try to guess which system produced which letter.",
            "",
        ]
        for lab in labels:
            meth = mapping[lab]
            ans = (item["methods"][meth].get("answer") or "").strip() or "_(empty)_"
            lines += [
                f"## Answer {lab}",
                "",
                ans,
                "",
                f"- Faithfulness (1–5): ___",
                f"- Usefulness (1–5): ___",
                f"- Technical correctness (1–5): ___",
                "",
            ]
        lines += [
            "## Preference rank (1=best … 4=worst)",
            "A: ___  B: ___  C: ___  D: ___",
            "",
        ]
        sheet_path = SHEETS_DIR / f"{qid}.md"
        sheet_path.write_text("\n".join(lines), encoding="utf-8")

        for lab in labels:
            rating_rows.append(
                {
                    "rater_id": "",
                    "question_id": qid,
                    "answer_label": lab,
                    "faithfulness": "",
                    "usefulness": "",
                    "technical_correctness": "",
                    "rank": "",
                    "notes": "",
                }
            )

    KEY_PATH.write_text(json.dumps(key, indent=2), encoding="utf-8")
    with RATINGS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rater_id",
                "question_id",
                "answer_label",
                "faithfulness",
                "usefulness",
                "technical_correctness",
                "rank",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rating_rows)

    print(f"Sheets: {SHEETS_DIR} ({len(list(SHEETS_DIR.glob('*.md')))} files)", flush=True)
    print(f"Key (keep secret): {KEY_PATH}", flush=True)
    print(f"Ratings CSV: {RATINGS_CSV}", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
