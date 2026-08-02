"""Retry failed smoke questions after context truncation fix."""

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

NEED = ["q019", "q032", "q041"]
ORDER = [
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


def main() -> None:
    out = root / "artifacts" / "evaluation" / "smoke_baseline_results.json"
    payload = json.loads(out.read_text(encoding="utf-8"))
    qs = {
        q.id: q
        for q in load_eval_dataset(
            root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
        )
    }

    retriever = Retriever()
    generator = AnswerGenerator()
    pipeline = RAGICOTPipeline()
    print("LLM", generator.llm.provider, generator.llm.model_name)

    errors = [e for e in payload.get("errors", []) if e["id"] not in NEED]

    for qid in NEED:
        q = qs[qid]
        print("RUNNING", qid)
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
            v = summarize_run(
                vanilla,
                q.required_facets,
                q.expected_sources,
                q.reference_hints,
            )
            i = summarize_run(
                icot,
                q.required_facets,
                q.expected_sources,
                q.reference_hints,
            )
            print(
                qid,
                "vanilla",
                v["facet_recall"],
                v["keyword_hit_rate"],
                v["source_hit_rate"],
            )
            print(
                qid,
                "icot",
                i["facet_recall"],
                i["keyword_hit_rate"],
                i["source_hit_rate"],
            )
            payload["rows"] = [r for r in payload["rows"] if r["id"] != qid]
            payload["rows"].append(
                {
                    "id": qid,
                    "category": q.category,
                    "required_facets": q.required_facets,
                    "expected_sources": q.expected_sources,
                    "reference_hints": q.reference_hints,
                    "vanilla": v,
                    "facet_icot": i,
                    "vanilla_answer_preview": vanilla["answer"][:400],
                    "icot_answer_preview": icot["answer"][:400],
                }
            )
        except Exception as exc:
            print("FAIL", qid, type(exc).__name__, exc)
            errors.append(
                {"id": qid, "error": f"{type(exc).__name__}: {exc}"}
            )
        time.sleep(10)

    by = {r["id"]: r for r in payload["rows"]}
    payload["rows"] = [by[i] for i in ORDER if i in by]
    payload["errors"] = errors
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    rows = payload["rows"]

    def avg(method: str, key: str) -> float:
        return sum(r[method][key] for r in rows) / len(rows)

    print("rows", len(rows), "errors", len(errors))
    print(
        "AVG vanilla",
        avg("vanilla", "facet_recall"),
        avg("vanilla", "keyword_hit_rate"),
        avg("vanilla", "source_hit_rate"),
    )
    print(
        "AVG icot",
        avg("facet_icot", "facet_recall"),
        avg("facet_icot", "keyword_hit_rate"),
        avg("facet_icot", "source_hit_rate"),
    )
    for r in rows:
        v, i = r["vanilla"], r["facet_icot"]
        print(
            f"{r['id']:<5} {r['category']:<14} "
            f"V {v['facet_recall']:.2f}/{v['keyword_hit_rate']:.2f}/{v['source_hit_rate']:.2f} "
            f"I {i['facet_recall']:.2f}/{i['keyword_hit_rate']:.2f}/{i['source_hit_rate']:.2f}"
        )


if __name__ == "__main__":
    main()
