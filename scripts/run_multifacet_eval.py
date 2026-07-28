"""Full multi-facet eval: vanilla RAG vs facet ICOT (iter=3, filtered answer context)."""

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
    run_vanilla_rag,
    summarize_judge_rows,
    summarize_run,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

PAUSE = 8
ICOT_ITERS = 3


def _preview(docs: list) -> str:
    return format_documents_for_llm(docs, max_docs=5, max_chars=400)


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
                q.question,
                k=5,
                retriever=retriever,
                generator=generator,
            )
            icot = run_facet_icot(
                q.question,
                max_iterations=ICOT_ITERS,
                pipeline=pipeline,
                required_facets=q.required_facets,
                filter_answer_context=True,
            )

            v_sum = summarize_run(
                vanilla,
                q.required_facets,
                q.expected_sources,
                q.reference_hints,
            )
            i_sum = summarize_run(
                icot,
                q.required_facets,
                q.expected_sources,
                q.reference_hints,
            )
            answer_docs = icot.get("answer_documents") or icot["documents"]
            i_sum["answer_doc_count"] = len(answer_docs)

            v_judge = judge.score(
                q.question,
                vanilla["answer"],
                gold_notes=q.gold_notes,
                reference_hints=q.reference_hints,
                evidence_preview=_preview(vanilla["documents"]),
            )
            time.sleep(2)
            i_judge = judge.score(
                q.question,
                icot["answer"],
                gold_notes=q.gold_notes,
                reference_hints=q.reference_hints,
                evidence_preview=_preview(answer_docs),
            )

            print(
                f"vanilla fac={v_sum['facet_recall']:.2f} "
                f"kw={v_sum['keyword_hit_rate']:.2f} "
                f"src={v_sum['source_hit_rate']:.2f} "
                f"judge={v_judge['overall']:.2f}",
                flush=True,
            )
            print(
                f"icot    fac={i_sum['facet_recall']:.2f} "
                f"kw={i_sum['keyword_hit_rate']:.2f} "
                f"src={i_sum['source_hit_rate']:.2f} "
                f"judge={i_judge['overall']:.2f} "
                f"answer_docs={len(answer_docs)}/{len(icot['documents'])}",
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
                    "vanilla": v_sum,
                    "facet_icot": i_sum,
                    "icot_answer_doc_ids": [d["id"] for d in answer_docs],
                    "judges": {
                        "vanilla": v_judge,
                        "facet_icot": i_judge,
                    },
                    "vanilla_answer_preview": vanilla["answer"][:450],
                    "icot_answer_preview": icot["answer"][:450],
                }
            )
        except Exception as exc:
            print(f"FAILED {q.id}: {type(exc).__name__}: {exc}", flush=True)
            errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})

        print(f"Sleeping {PAUSE}s...", flush=True)
        time.sleep(PAUSE)

    judge_summary = summarize_judge_rows(rows)

    def avg(method: str, key: str) -> float:
        if not rows:
            return 0.0
        return sum(r[method][key] for r in rows) / len(rows)

    hard_summary = {
        "vanilla": {
            "facet_recall": avg("vanilla", "facet_recall"),
            "keyword_hit_rate": avg("vanilla", "keyword_hit_rate"),
            "source_hit_rate": avg("vanilla", "source_hit_rate"),
        },
        "facet_icot": {
            "facet_recall": avg("facet_icot", "facet_recall"),
            "keyword_hit_rate": avg("facet_icot", "keyword_hit_rate"),
            "source_hit_rate": avg("facet_icot", "source_hit_rate"),
        },
        "n": len(rows),
    }

    wins = {"vanilla": 0, "facet_icot": 0, "tie": 0}
    for r in rows:
        v = r["judges"]["vanilla"]["overall"]
        i = r["judges"]["facet_icot"]["overall"]
        if abs(v - i) < 1e-9:
            wins["tie"] += 1
        elif v > i:
            wins["vanilla"] += 1
        else:
            wins["facet_icot"] += 1

    payload = {
        "config": {
            "category": "multi_facet",
            "icot_max_iterations": ICOT_ITERS,
            "answer_context_filtered": True,
            "n_questions": len(questions),
        },
        "rows": rows,
        "errors": errors,
        "hard_summary": hard_summary,
        "judge_summary": judge_summary,
        "judge_wins": wins,
    }

    out = root / "artifacts" / "evaluation" / "multifacet_vanilla_vs_icot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nHARD", json.dumps(hard_summary, indent=2), flush=True)
    print("JUDGE", json.dumps(judge_summary, indent=2), flush=True)
    print("WINS", wins, flush=True)
    print("Saved", out, "rows=", len(rows), "errors=", len(errors), flush=True)


if __name__ == "__main__":
    main()
