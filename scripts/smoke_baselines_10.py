"""Run ~10-question baseline smoke with keyword/source hit metrics."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.components.answer_generator import AnswerGenerator
from rag_icot.components.retriever import Retriever
from rag_icot.evaluation import (
    load_eval_dataset,
    run_facet_icot,
    run_vanilla_rag,
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
PAUSE_SECONDS = 8


def main() -> None:
    questions = load_eval_dataset(
        root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
    )
    by_id = {q.id: q for q in questions}
    smoke = [by_id[i] for i in SMOKE_IDS if i in by_id]

    retriever = Retriever()
    generator = AnswerGenerator()
    pipeline = RAGICOTPipeline()
    print("LLM ready:", generator.llm.provider, generator.llm.model_name)
    print("Smoke size:", len(smoke))

    rows = []
    errors = []

    for q in smoke:
        print("\n" + "=" * 80)
        print("QUESTION", q.id, q.question)
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
            )
            v_sum = summarize_run(
                vanilla,
                required_facets=q.required_facets,
                expected_sources=q.expected_sources,
                reference_hints=q.reference_hints,
            )
            i_sum = summarize_run(
                icot,
                required_facets=q.required_facets,
                expected_sources=q.expected_sources,
                reference_hints=q.reference_hints,
            )
            print(
                f"vanilla fac={v_sum['facet_recall']:.2f} "
                f"kw={v_sum['keyword_hit_rate']:.2f} "
                f"src={v_sum['source_hit_rate']:.2f}"
            )
            print(
                f"icot    fac={i_sum['facet_recall']:.2f} "
                f"kw={i_sum['keyword_hit_rate']:.2f} "
                f"src={i_sum['source_hit_rate']:.2f}"
            )
            rows.append(
                {
                    "id": q.id,
                    "category": q.category,
                    "required_facets": q.required_facets,
                    "expected_sources": q.expected_sources,
                    "reference_hints": q.reference_hints,
                    "vanilla": v_sum,
                    "facet_icot": i_sum,
                    "vanilla_answer_preview": vanilla["answer"][:400],
                    "icot_answer_preview": icot["answer"][:400],
                }
            )
        except Exception as exc:
            print(f"FAILED {q.id}: {type(exc).__name__}: {exc}")
            errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})

        print(f"Sleeping {PAUSE_SECONDS}s...")
        time.sleep(PAUSE_SECONDS)

    out = root / "artifacts" / "evaluation" / "smoke_baseline_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rows": rows, "errors": errors}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if rows:
        def avg(method: str, key: str) -> float:
            return sum(r[method][key] for r in rows) / len(rows)

        print("\nAVG vanilla fac/kw/src:",
              f"{avg('vanilla','facet_recall'):.2f}",
              f"{avg('vanilla','keyword_hit_rate'):.2f}",
              f"{avg('vanilla','source_hit_rate'):.2f}")
        print("AVG icot    fac/kw/src:",
              f"{avg('facet_icot','facet_recall'):.2f}",
              f"{avg('facet_icot','keyword_hit_rate'):.2f}",
              f"{avg('facet_icot','source_hit_rate'):.2f}")

    print("Saved", out, "rows=", len(rows), "errors=", len(errors))


if __name__ == "__main__":
    main()
