"""3-way multi-facet compare: vanilla vs prompt-only ICoT vs facet ICOT."""

from __future__ import annotations

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
    run_facet_icot,
    run_prompt_only_icot,
    run_vanilla_rag,
    summarize_run,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

PAUSE = 8
ICOT_ITERS = 3


def _preview(docs: list) -> str:
    if not docs:
        return "(no retrieved evidence — prompt-only baseline)"
    return format_documents_for_llm(docs, max_docs=5, max_chars=400)


def _avg(rows: list, method: str, key: str) -> float:
    if not rows:
        return 0.0
    return sum(r[method][key] for r in rows) / len(rows)


def main() -> None:
    questions = [
        q
        for q in load_eval_dataset(
            root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
        )
        if q.category == "multi_facet"
    ]
    print(f"Multi-facet questions: {len(questions)}", flush=True)

    print("Loading pipeline...", flush=True)
    pipeline = RAGICOTPipeline()
    retriever = pipeline.engine.retriever
    generator = pipeline.generator
    judge = AnswerJudge(llm=generator.llm)
    print("LLM", generator.llm.provider, generator.llm.model_name, flush=True)

    rows = []
    errors = []

    for q in questions:
        print("\n" + "=" * 80, flush=True)
        print(q.id, q.required_facets, q.question, flush=True)
        print("=" * 80, flush=True)
        try:
            vanilla = run_vanilla_rag(
                q.question, k=5, retriever=retriever, generator=generator
            )
            prompt = run_prompt_only_icot(q.question, llm=generator.llm)
            icot = run_facet_icot(
                q.question,
                max_iterations=ICOT_ITERS,
                pipeline=pipeline,
                required_facets=q.required_facets,
                filter_answer_context=True,
            )

            methods = {
                "vanilla": vanilla,
                "prompt_only_icot": prompt,
                "facet_icot": icot,
            }
            summaries = {}
            judges = {}

            for name, run in methods.items():
                summaries[name] = summarize_run(
                    run,
                    required_facets=q.required_facets,
                    expected_sources=q.expected_sources,
                    reference_hints=q.reference_hints,
                )
                docs = run.get("answer_documents") or run.get("documents") or []
                if name == "facet_icot":
                    summaries[name]["answer_doc_count"] = len(docs)

                judges[name] = judge.score(
                    q.question,
                    run["answer"],
                    gold_notes=q.gold_notes,
                    reference_hints=q.reference_hints,
                    evidence_preview=_preview(docs),
                )
                time.sleep(2)
                print(
                    f"{name:18s} fac={summaries[name]['facet_recall']:.2f} "
                    f"kw={summaries[name]['keyword_hit_rate']:.2f} "
                    f"src={summaries[name]['source_hit_rate']:.2f} "
                    f"judge={judges[name]['overall']:.2f}",
                    flush=True,
                )

            rows.append(
                {
                    "id": q.id,
                    "category": q.category,
                    "question": q.question,
                    "required_facets": q.required_facets,
                    "expected_sources": q.expected_sources,
                    "reference_hints": q.reference_hints,
                    "vanilla": summaries["vanilla"],
                    "prompt_only_icot": summaries["prompt_only_icot"],
                    "facet_icot": summaries["facet_icot"],
                    "judges": judges,
                    "vanilla_answer_preview": vanilla["answer"][:400],
                    "prompt_only_answer_preview": prompt["answer"][:400],
                    "icot_answer_preview": icot["answer"][:400],
                }
            )
        except Exception as exc:
            print(f"FAILED {q.id}: {type(exc).__name__}: {exc}", flush=True)
            errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})

        print(f"Sleeping {PAUSE}s...", flush=True)
        time.sleep(PAUSE)

    methods = ["vanilla", "prompt_only_icot", "facet_icot"]
    hard_summary = {
        m: {
            "facet_recall": _avg(rows, m, "facet_recall"),
            "keyword_hit_rate": _avg(rows, m, "keyword_hit_rate"),
            "source_hit_rate": _avg(rows, m, "source_hit_rate"),
        }
        for m in methods
    }
    hard_summary["n"] = len(rows)

    judge_summary = {}
    for m in methods:
        dims = ["reliability", "relevance", "technicality", "friendliness", "overall"]
        judge_summary[m] = {
            d: (
                sum(r["judges"][m][d] for r in rows) / len(rows) if rows else 0.0
            )
            for d in dims
        }
        judge_summary[m]["n"] = len(rows)

    # Best overall judge wins
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

    payload = {
        "config": {
            "category": "multi_facet",
            "baselines": methods,
            "icot_max_iterations": ICOT_ITERS,
            "answer_context_filtered": True,
            "n_questions": len(questions),
        },
        "rows": rows,
        "errors": errors,
        "hard_summary": hard_summary,
        "judge_summary": judge_summary,
        "judge_wins": wins,
        "judge_ties": ties,
    }

    out = root / "artifacts" / "evaluation" / "multifacet_three_way.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nHARD", json.dumps(hard_summary, indent=2), flush=True)
    print("JUDGE", json.dumps(judge_summary, indent=2), flush=True)
    print("WINS", wins, "ties", ties, flush=True)
    print("Saved", out, "rows=", len(rows), "errors=", len(errors), flush=True)


if __name__ == "__main__":
    main()
