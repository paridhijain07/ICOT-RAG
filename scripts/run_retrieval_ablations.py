import json
import os
import sys

sys.path.insert(0, ".")

from rag_icot.components.retriever import Retriever
from rag_icot.evaluation import (
    load_eval_dataset,
    RETRIEVAL_ABLATIONS,
    run_retrieval_ablation,
    summarize_ablation_table,
)


def main():
    qs = load_eval_dataset("datasets/evaluation/iot_security_eval_v1.json")
    ids = [
        "q001", "q002", "q011", "q019", "q021",
        "q025", "q031", "q033", "q041", "q050",
    ]
    subset = [q for q in qs if q.id in ids]
    retriever = Retriever()
    rows = []

    for q in subset:
        for cfg in RETRIEVAL_ABLATIONS:
            row = run_retrieval_ablation(
                q.question,
                q.required_facets,
                cfg,
                retriever=retriever,
            )
            row["question_id"] = q.id
            row["category"] = q.category
            rows.append(row)

    summary = summarize_ablation_table(rows)
    print(f"{'Ablation':<28} {'N':>4} {'Mean':>8}")
    for item in summary:
        print(
            f"{item['ablation_name']:<28} "
            f"{item['n']:>4} "
            f"{item['mean_facet_recall']:>8.3f}"
        )

    os.makedirs("artifacts/evaluation", exist_ok=True)
    out = "artifacts/evaluation/retrieval_ablations.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)
    print("saved", out, "rows=", len(rows))


if __name__ == "__main__":
    main()
