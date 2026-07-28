"""Quick post-fix smoke for q001/q011 (retrieval + optional LLM)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.components.answer_generator import AnswerGenerator
from rag_icot.components.retriever import Retriever
from rag_icot.evaluation.baselines import run_facet_icot, run_vanilla_rag
from rag_icot.evaluation.metrics import summarize_run
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline


def keyword_hit(run: dict, needle: str) -> bool:
    blob = " ".join(
        (d.get("text") or "") + " " + json.dumps(d.get("metadata") or {})
        for d in run.get("documents", [])
    )
    return needle.lower() in blob.lower()


def main() -> None:
    retriever = Retriever()
    generator = AnswerGenerator()
    pipeline = RAGICOTPipeline()
    print("LLM provider:", generator.llm.provider, generator.llm.model_name)

    cases = [
        (
            "q001",
            "What network behaviours does Mirai show in the IoT-23 Capture-7-1 scenario?",
            ["behaviour"],
            "Mirai",
        ),
        (
            "q011",
            "What is CVE-2020-8863 about and which products are affected?",
            ["vulnerability"],
            "CVE-2020-8863",
        ),
    ]

    rows = []
    for qid, question, facets, needle in cases:
        print("\n" + "=" * 80)
        print(qid, question)
        vanilla = run_vanilla_rag(
            question, k=5, retriever=retriever, generator=generator
        )
        icot = run_facet_icot(question, max_iterations=2, pipeline=pipeline)

        v_sum = summarize_run(vanilla, facets)
        i_sum = summarize_run(icot, facets)
        v_hit = keyword_hit(vanilla, needle)
        i_hit = keyword_hit(icot, needle)

        print("vanilla:", v_sum, "keyword_hit=", v_hit)
        print("facet_icot:", i_sum, "keyword_hit=", i_hit)
        print("vanilla docs:", [d["id"] for d in vanilla["documents"]])
        print("icot docs:", [d["id"] for d in icot["documents"]][:8], "...")
        print("vanilla ans:", vanilla["answer"][:280].replace("\n", " "))
        print("icot ans:", icot["answer"][:280].replace("\n", " "))

        rows.append(
            {
                "id": qid,
                "vanilla": v_sum,
                "facet_icot": i_sum,
                "vanilla_keyword_hit": v_hit,
                "icot_keyword_hit": i_hit,
                "vanilla_doc_ids": [d["id"] for d in vanilla["documents"]],
                "icot_doc_ids": [d["id"] for d in icot["documents"]],
                "vanilla_answer_preview": vanilla["answer"][:400],
                "icot_answer_preview": icot["answer"][:400],
            }
        )

    out = root / "artifacts" / "evaluation" / "smoke_baseline_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows, "errors": []}, indent=2), encoding="utf-8")
    print("\nSaved", out)


if __name__ == "__main__":
    main()
