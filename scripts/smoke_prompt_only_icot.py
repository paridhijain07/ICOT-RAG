"""Smoke-test Zeng-style prompt-only ICoT on 2 questions (no retrieval)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.evaluation import (
    load_eval_dataset,
    run_prompt_only_icot,
    summarize_run,
)


def main() -> None:
    by_id = {
        q.id: q
        for q in load_eval_dataset(
            root / "datasets" / "evaluation" / "iot_security_eval_v1.json"
        )
    }
    ids = ["q001", "q011"]
    rows = []

    for qid in ids:
        q = by_id[qid]
        print("=" * 80)
        print(qid, q.question)
        result = run_prompt_only_icot(q.question)
        summary = summarize_run(
            result,
            required_facets=q.required_facets,
            expected_sources=q.expected_sources,
            reference_hints=q.reference_hints,
        )
        print(
            "baseline=",
            result["baseline"],
            "iters=",
            result["iterations"],
            "docs=",
            len(result["documents"]),
            "fac=",
            summary["facet_recall"],
            "kw=",
            summary["keyword_hit_rate"],
        )
        print("answer preview:", result["answer"][:350].replace("\n", " "))
        rows.append(
            {
                "id": qid,
                "summary": summary,
                "answer_preview": result["answer"][:500],
                "trace_stages": [t.get("stage") for t in result["trace"]],
            }
        )

    out = root / "artifacts" / "evaluation" / "prompt_only_icot_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print("Saved", out)


if __name__ == "__main__":
    main()
