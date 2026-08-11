"""Full-set three/four-way eval with resume support.

Examples:
  python scripts/run_full_eval.py --limit 3
  python scripts/run_full_eval.py --category multi_facet
  python scripts/run_full_eval.py --four-way
  python scripts/run_full_eval.py --resume
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.components.context_format import format_documents_for_llm
from rag_icot.evaluation import (
    AnswerJudge,
    load_eval_dataset,
    run_chatiot_style,
    run_facet_icot,
    run_prompt_only_icot,
    run_vanilla_rag,
    summarize_run,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

PAUSE = 6
ICOT_ITERS = 3
DATASET = root / "datasets" / "evaluation" / "iot_security_eval_v1.json"


def _is_rate_limit(exc: BaseException) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    return (
        "ratelimit" in name.lower()
        or "rate_limit" in msg
        or "rate limit" in msg
        or "429" in msg
        or "tokens per day" in msg
        or "tpd" in msg
    )


def _rate_limit_sleep_seconds(exc: BaseException, fallback: float = 120.0) -> float:
    """Parse Groq 'try again in XmYs' if present."""
    import re

    msg = str(exc)
    m = re.search(
        r"try again in\s+(?:(\d+)m)?\s*([\d.]+)s",
        msg,
        flags=re.IGNORECASE,
    )
    if not m:
        return fallback
    minutes = int(m.group(1) or 0)
    seconds = float(m.group(2) or 0)
    return max(fallback, minutes * 60 + seconds + 5)


def _preview(docs: list) -> str:
    if not docs:
        return "(no retrieved evidence — prompt-only baseline)"
    return format_documents_for_llm(docs, max_docs=5, max_chars=400)


def _avg(rows: list, method: str, key: str) -> float:
    if not rows:
        return 0.0
    return sum(r[method][key] for r in rows) / len(rows)


def _summarize(rows: list, methods: list[str]) -> dict:
    hard_summary = {
        m: {
            "facet_recall": _avg(rows, m, "facet_recall"),
            "facet_recall_at_budget": _avg(rows, m, "facet_recall_at_budget"),
            "keyword_hit_rate": _avg(rows, m, "keyword_hit_rate"),
            "source_hit_rate": _avg(rows, m, "source_hit_rate"),
            "faithfulness_rate": _avg(rows, m, "faithfulness_rate"),
            "doc_count": _avg(rows, m, "doc_count"),
            "answer_doc_count": _avg(rows, m, "answer_doc_count"),
        }
        for m in methods
    }
    hard_summary["n"] = len(rows)

    dims = ["reliability", "relevance", "technicality", "friendliness", "overall"]
    judge_summary = {}
    for m in methods:
        judge_summary[m] = {
            d: (sum(r["judges"][m][d] for r in rows) / len(rows) if rows else 0.0)
            for d in dims
        }
        judge_summary[m]["n"] = len(rows)

    wins = {m: 0 for m in methods}
    ties = 0
    for r in rows:
        scores = {m: r["judges"][m]["overall"] for m in methods}
        best = max(scores.values())
        leaders = [m for m, s in scores.items() if abs(s - best) < 1e-9]
        if len(leaders) > 1:
            ties += 1
        else:
            wins[leaders[0]] += 1

    by_category: dict[str, dict] = {}
    cats = sorted({r["category"] for r in rows})
    for cat in cats:
        sub = [r for r in rows if r["category"] == cat]
        by_category[cat] = {
            "n": len(sub),
            "hard": {
                m: {
                    "facet_recall": _avg(sub, m, "facet_recall"),
                    "facet_recall_at_budget": _avg(sub, m, "facet_recall_at_budget"),
                    "source_hit_rate": _avg(sub, m, "source_hit_rate"),
                    "keyword_hit_rate": _avg(sub, m, "keyword_hit_rate"),
                    "faithfulness_rate": _avg(sub, m, "faithfulness_rate"),
                }
                for m in methods
            },
            "judge_overall": {
                m: (
                    sum(r["judges"][m]["overall"] for r in sub) / len(sub)
                    if sub
                    else 0.0
                )
                for m in methods
            },
        }

    return {
        "hard_summary": hard_summary,
        "judge_summary": judge_summary,
        "judge_wins": wins,
        "judge_ties": ties,
        "by_category": by_category,
    }


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full ICOT-RAG baseline eval")
    parser.add_argument(
        "--category",
        default="all",
        help="all | multi_facet | behaviour | …",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max questions (0=all)")
    parser.add_argument(
        "--four-way",
        action="store_true",
        help="Include ChatIoT-style multi-retriever baseline",
    )
    parser.add_argument("--resume", action="store_true", help="Skip completed ids")
    parser.add_argument(
        "--out",
        default="",
        help="Output JSON path (default under artifacts/evaluation/)",
    )
    parser.add_argument("--pause", type=float, default=PAUSE)
    parser.add_argument(
        "--max-retries",
        type=int,
        default=6,
        help="Retries per question on rate-limit errors",
    )
    args = parser.parse_args()

    methods = ["vanilla", "prompt_only_icot", "facet_icot"]
    if args.four_way:
        methods = ["vanilla", "prompt_only_icot", "chatiot_style", "facet_icot"]

    default_name = (
        "full_four_way.json" if args.four_way else "full_three_way.json"
    )
    if args.category != "all" and not args.out:
        default_name = f"{args.category}_{'four' if args.four_way else 'three'}_way.json"
    out = Path(args.out) if args.out else root / "artifacts" / "evaluation" / default_name

    questions = load_eval_dataset(DATASET)
    if args.category != "all":
        questions = [q for q in questions if q.category == args.category]
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]

    rows: list[dict] = []
    errors: list[dict] = []
    done_ids: set[str] = set()

    if args.resume and out.exists():
        prev = json.loads(out.read_text(encoding="utf-8"))
        rows = list(prev.get("rows") or [])
        done_ids = {r["id"] for r in rows}
        # Drop errors for ids we will retry (e.g. prior rate limits)
        errors = [
            e for e in (prev.get("errors") or []) if e.get("id") in done_ids
        ]
        print(f"Resume: {len(done_ids)} rows already in {out}", flush=True)

    print(
        f"Questions: {len(questions)} | methods={methods} | out={out}",
        flush=True,
    )
    print("Loading pipeline...", flush=True)
    pipeline = RAGICOTPipeline()
    retriever = pipeline.engine.retriever
    generator = pipeline.generator
    judge = AnswerJudge(llm=generator.llm)
    print("LLM", generator.llm.provider, generator.llm.model_name, flush=True)

    for q in questions:
        if q.id in done_ids:
            continue

        print("\n" + "=" * 80, flush=True)
        print(q.id, q.category, q.required_facets, flush=True)
        print(q.question, flush=True)
        print("=" * 80, flush=True)

        attempt = 0
        while True:
            attempt += 1
            try:
                runs = {
                    "vanilla": run_vanilla_rag(
                        q.question, k=5, retriever=retriever, generator=generator
                    ),
                    "prompt_only_icot": run_prompt_only_icot(
                        q.question, llm=generator.llm
                    ),
                    "facet_icot": run_facet_icot(
                        q.question,
                        max_iterations=ICOT_ITERS,
                        pipeline=pipeline,
                        required_facets=q.required_facets,
                        filter_answer_context=True,
                    ),
                }
                if "chatiot_style" in methods:
                    runs["chatiot_style"] = run_chatiot_style(
                        q.question,
                        k_per_source=3,
                        max_docs=8,
                        retriever=retriever,
                        generator=generator,
                    )

                summaries = {}
                judges = {}
                for name in methods:
                    run = runs[name]
                    summaries[name] = summarize_run(
                        run,
                        required_facets=q.required_facets,
                        expected_sources=q.expected_sources,
                        reference_hints=q.reference_hints,
                    )
                    docs = run.get("answer_documents") or run.get("documents") or []
                    judges[name] = judge.score(
                        q.question,
                        run["answer"],
                        gold_notes=q.gold_notes,
                        reference_hints=q.reference_hints,
                        evidence_preview=_preview(docs),
                    )
                    time.sleep(1.5)
                    print(
                        f"{name:18s} fac={summaries[name]['facet_recall']:.2f} "
                        f"fac@6={summaries[name]['facet_recall_at_budget']:.2f} "
                        f"faith={summaries[name]['faithfulness_rate']:.2f} "
                        f"src={summaries[name]['source_hit_rate']:.2f} "
                        f"judge={judges[name]['overall']:.2f}",
                        flush=True,
                    )

                row = {
                    "id": q.id,
                    "category": q.category,
                    "question": q.question,
                    "required_facets": q.required_facets,
                    "expected_sources": q.expected_sources,
                    "reference_hints": q.reference_hints,
                    "judges": judges,
                }
                for name in methods:
                    row[name] = summaries[name]
                    row[f"{name}_answer_preview"] = runs[name]["answer"][:400]
                rows.append(row)
                done_ids.add(q.id)
                break
            except Exception as exc:
                if _is_rate_limit(exc) and attempt <= args.max_retries:
                    wait = _rate_limit_sleep_seconds(exc, fallback=180.0)
                    print(
                        f"RATE LIMIT {q.id} attempt {attempt}/{args.max_retries}; "
                        f"sleeping {wait:.0f}s...",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                print(f"FAILED {q.id}: {type(exc).__name__}: {exc}", flush=True)
                errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})
                break

        stats = _summarize(rows, methods)
        payload = {
            "config": {
                "category": args.category,
                "baselines": methods,
                "icot_max_iterations": ICOT_ITERS,
                "answer_context_filtered": True,
                "icot_multisource_init": True,
                "facet_budget_docs": 6,
                "chatiot_k_per_source": 3 if args.four_way else None,
                "chatiot_max_docs": 8 if args.four_way else None,
                "n_questions_target": len(questions),
                "llm_provider": generator.llm.provider,
                "llm_model": generator.llm.model_name,
            },
            "rows": rows,
            "errors": errors,
            **stats,
        }
        _save(out, payload)
        print(
            f"Saved {out} rows={len(rows)} errors={len(errors)}",
            flush=True,
        )
        print(f"Sleeping {args.pause}s...", flush=True)
        time.sleep(args.pause)

    stats = _summarize(rows, methods)
    print("\nHARD", json.dumps(stats["hard_summary"], indent=2), flush=True)
    print("JUDGE", json.dumps(stats["judge_summary"], indent=2), flush=True)
    print("WINS", stats["judge_wins"], "ties", stats["judge_ties"], flush=True)
    print("BY CATEGORY", json.dumps(stats["by_category"], indent=2), flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
