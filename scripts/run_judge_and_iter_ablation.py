"""LLM-as-judge on smoke answers + max_iter ablation on multi-facet questions."""

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
    LLM_ABLATIONS,
    AnswerJudge,
    load_eval_dataset,
    run_facet_icot,
    run_llm_ablation,
    run_vanilla_rag,
    summarize_judge_rows,
    summarize_run,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

SMOKE_IDS = [
    "q001",
    "q002",
    "q011",
    "q012",
    "q019",
    "q021",
    "q025",
    "q031",
    "q032",
    "q041",
]
MULTI_FACET_IDS = ["q031", "q032", "q033", "q034"]
PAUSE = 8


def _evidence_preview(documents: list) -> str:
    return format_documents_for_llm(documents, max_docs=5, max_chars=400)


def run_judge_smoke(questions_by_id, retriever, generator, pipeline, judge):
    rows = []
    errors = []

    for qid in SMOKE_IDS:
        q = questions_by_id[qid]
        print("\n" + "=" * 80)
        print("JUDGE SMOKE", qid, q.question)
        print("=" * 80)
        try:
            vanilla = run_vanilla_rag(
                q.question,
                k=5,
                retriever=retriever,
                generator=generator,
            )
            icot = run_facet_icot(
                q.question,
                max_iterations=2,
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

            icot_answer_docs = icot.get("answer_documents") or icot["documents"]
            i_sum["answer_doc_count"] = len(icot_answer_docs)

            v_judge = judge.score(
                question=q.question,
                answer=vanilla["answer"],
                gold_notes=q.gold_notes,
                reference_hints=q.reference_hints,
                evidence_preview=_evidence_preview(vanilla["documents"]),
            )
            time.sleep(2)
            i_judge = judge.score(
                question=q.question,
                answer=icot["answer"],
                gold_notes=q.gold_notes,
                reference_hints=q.reference_hints,
                evidence_preview=_evidence_preview(icot_answer_docs),
            )

            print(
                f"vanilla overall={v_judge['overall']:.2f} "
                f"fac={v_sum['facet_recall']:.2f} kw={v_sum['keyword_hit_rate']:.2f}"
            )
            print(
                f"icot    overall={i_judge['overall']:.2f} "
                f"fac={i_sum['facet_recall']:.2f} kw={i_sum['keyword_hit_rate']:.2f} "
                f"answer_docs={len(icot_answer_docs)}/{len(icot['documents'])}"
            )

            rows.append(
                {
                    "id": q.id,
                    "category": q.category,
                    "question": q.question,
                    "vanilla": v_sum,
                    "facet_icot": i_sum,
                    "icot_answer_doc_ids": [d["id"] for d in icot_answer_docs],
                    "judges": {
                        "vanilla": v_judge,
                        "facet_icot": i_judge,
                    },
                    "vanilla_answer_preview": vanilla["answer"][:500],
                    "icot_answer_preview": icot["answer"][:500],
                }
            )
        except Exception as exc:
            print(f"FAILED {qid}: {type(exc).__name__}: {exc}")
            errors.append({"id": qid, "error": f"{type(exc).__name__}: {exc}"})

        print(f"Sleeping {PAUSE}s...")
        time.sleep(PAUSE)

    return rows, errors


def run_iter_ablation(questions_by_id, retriever, generator, pipeline, judge):
    rows = []
    errors = []
    configs = [c for c in LLM_ABLATIONS]

    for qid in MULTI_FACET_IDS:
        q = questions_by_id[qid]
        print("\n" + "=" * 80)
        print("ITER ABLATION", qid, q.question)
        print("=" * 80)
        q_row = {
            "id": q.id,
            "category": q.category,
            "question": q.question,
            "required_facets": q.required_facets,
            "ablations": {},
        }
        try:
            for cfg in configs:
                print(f"  -> {cfg.id}")
                result = run_llm_ablation(
                    q.question,
                    cfg,
                    required_facets=q.required_facets,
                    expected_sources=q.expected_sources,
                    reference_hints=q.reference_hints,
                    retriever=retriever,
                    generator=generator,
                    pipeline=pipeline,
                )
                j = judge.score(
                    question=q.question,
                    answer=result["answer"],
                    gold_notes=q.gold_notes,
                    reference_hints=q.reference_hints,
                    evidence_preview=_evidence_preview(
                        result.get("answer_documents") or result["documents"]
                    ),
                )
                q_row["ablations"][cfg.id] = {
                    "ablation_name": cfg.name,
                    "facet_recall": result["facet_recall"],
                    "keyword_hit_rate": result["keyword_hit_rate"],
                    "source_hit_rate": result["source_hit_rate"],
                    "iterations": result["iterations"],
                    "doc_count": result["doc_count"],
                    "answer_doc_count": len(
                        result.get("answer_documents") or result["documents"]
                    ),
                    "sources": result["sources"],
                    "judge": j,
                    "answer_preview": result["answer"][:400],
                }
                print(
                    f"     fac={result['facet_recall']:.2f} "
                    f"kw={result['keyword_hit_rate']:.2f} "
                    f"judge={j['overall']:.2f}"
                )
                time.sleep(3)
            rows.append(q_row)
        except Exception as exc:
            print(f"FAILED {qid}: {type(exc).__name__}: {exc}")
            errors.append({"id": qid, "error": f"{type(exc).__name__}: {exc}"})
            if q_row["ablations"]:
                rows.append(q_row)

        print(f"Sleeping {PAUSE}s...")
        time.sleep(PAUSE)

    return rows, errors


def main() -> None:
    questions = load_eval_dataset(
        root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
    )
    by_id = {q.id: q for q in questions}

    # One pipeline = one embedder + shared generator (avoids HF reload hangs)
    print("Loading pipeline (single embedding model)...", flush=True)
    pipeline = RAGICOTPipeline()
    retriever = pipeline.engine.retriever
    generator = pipeline.generator
    judge = AnswerJudge(llm=generator.llm)
    print(
        "LLM",
        generator.llm.provider,
        generator.llm.model_name,
        flush=True,
    )

    out_dir = root / "artifacts" / "evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)

    judge_rows, judge_errors = run_judge_smoke(
        by_id, retriever, generator, pipeline, judge
    )
    judge_summary = summarize_judge_rows(judge_rows)
    judge_path = out_dir / "llm_judge_smoke.json"
    judge_path.write_text(
        json.dumps(
            {
                "config": {
                    "answer_context_filtered": True,
                    "icot_max_iterations": 2,
                    "smoke_ids": SMOKE_IDS,
                },
                "rows": judge_rows,
                "errors": judge_errors,
                "summary": judge_summary,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print("\nJudge summary:", json.dumps(judge_summary, indent=2))
    print("Saved", judge_path)

    ablate_rows, ablate_errors = run_iter_ablation(
        by_id, retriever, generator, pipeline, judge
    )
    # Aggregate means per ablation id
    from collections import defaultdict

    agg: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in ablate_rows:
        for aid, payload in row["ablations"].items():
            agg[aid]["facet_recall"].append(payload["facet_recall"])
            agg[aid]["keyword_hit_rate"].append(payload["keyword_hit_rate"])
            agg[aid]["source_hit_rate"].append(payload["source_hit_rate"])
            agg[aid]["judge_overall"].append(payload["judge"]["overall"])

    ablate_summary = {
        aid: {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}
        | {"n": len(next(iter(metrics.values()), []))}
        for aid, metrics in agg.items()
    }

    ablate_path = out_dir / "llm_iter_ablation.json"
    ablate_path.write_text(
        json.dumps(
            {
                "config": {
                    "answer_context_filtered": True,
                    "multi_facet_ids": MULTI_FACET_IDS,
                },
                "rows": ablate_rows,
                "errors": ablate_errors,
                "summary": ablate_summary,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print("\nIter ablation summary:", json.dumps(ablate_summary, indent=2))
    print("Saved", ablate_path)


if __name__ == "__main__":
    main()
