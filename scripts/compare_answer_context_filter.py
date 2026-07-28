"""Fair compare: one ICOT retrieval, answer from full vs filtered context."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.components.answer_context import select_answer_documents
from rag_icot.components.context_format import format_documents_for_llm
from rag_icot.evaluation import AnswerJudge, load_eval_dataset
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

COMPARE_IDS = ["q002", "q011", "q021", "q031", "q032"]
PAUSE = 5


def main() -> None:
    by_id = {
        q.id: q
        for q in load_eval_dataset(
            root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
        )
    }
    pipeline = RAGICOTPipeline()
    judge = AnswerJudge(llm=pipeline.generator.llm)
    print("LLM", pipeline.generator.llm.provider, flush=True)

    rows = []
    for qid in COMPARE_IDS:
        q = by_id[qid]
        print("\n" + "=" * 80)
        print(qid, q.question)
        print("=" * 80)

        reasoned = pipeline.engine.reason(q.question, max_iterations=2)
        all_docs = reasoned["documents"]
        covered = reasoned.get("covered_facets", [])
        filtered_docs = select_answer_documents(
            all_docs,
            question=q.question,
            covered_facets=covered,
            required_facets=q.required_facets,
            max_per_facet=2,
            max_total=6,
        )

        print(
            f"retrieved={len(all_docs)} filtered={len(filtered_docs)} "
            f"ids={[d['id'] for d in filtered_docs]}",
            flush=True,
        )

        ans_full = pipeline.generator.generate(q.question, all_docs)
        time.sleep(2)
        ans_filt = pipeline.generator.generate(q.question, filtered_docs)

        j_full = judge.score(
            q.question,
            ans_full,
            gold_notes=q.gold_notes,
            reference_hints=q.reference_hints,
            evidence_preview=format_documents_for_llm(
                all_docs, max_docs=6, max_chars=350
            ),
        )
        time.sleep(2)
        j_filt = judge.score(
            q.question,
            ans_filt,
            gold_notes=q.gold_notes,
            reference_hints=q.reference_hints,
            evidence_preview=format_documents_for_llm(
                filtered_docs, max_docs=6, max_chars=350
            ),
        )

        delta = j_filt["overall"] - j_full["overall"]
        print(
            f"judge full={j_full['overall']:.2f} "
            f"filtered={j_filt['overall']:.2f} delta={delta:+.2f}",
            flush=True,
        )

        rows.append(
            {
                "id": qid,
                "category": q.category,
                "retrieved_docs": len(all_docs),
                "filtered_answer_docs": len(filtered_docs),
                "filtered_ids": [d["id"] for d in filtered_docs],
                "judges": {"full_context": j_full, "filtered": j_filt},
                "full_preview": ans_full[:350],
                "filtered_preview": ans_filt[:350],
            }
        )
        time.sleep(PAUSE)

    n = len(rows)
    avg_full = sum(r["judges"]["full_context"]["overall"] for r in rows) / n
    avg_filt = sum(r["judges"]["filtered"]["overall"] for r in rows) / n
    summary = {
        "n": n,
        "avg_full_context": avg_full,
        "avg_filtered": avg_filt,
        "delta": avg_filt - avg_full,
        "wins_filtered": sum(
            1
            for r in rows
            if r["judges"]["filtered"]["overall"]
            > r["judges"]["full_context"]["overall"]
        ),
        "wins_full": sum(
            1
            for r in rows
            if r["judges"]["full_context"]["overall"]
            > r["judges"]["filtered"]["overall"]
        ),
        "ties": sum(
            1
            for r in rows
            if r["judges"]["filtered"]["overall"]
            == r["judges"]["full_context"]["overall"]
        ),
    }
    out = root / "artifacts" / "evaluation" / "answer_context_filter_compare.json"
    out.write_text(
        json.dumps({"rows": rows, "summary": summary}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\nSUMMARY", json.dumps(summary, indent=2), flush=True)
    print("Saved", out, flush=True)


if __name__ == "__main__":
    main()
