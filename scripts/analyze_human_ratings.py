"""Aggregate filled human ratings with the secret key.

Usage:
  python scripts/analyze_human_ratings.py paper/human_eval/ratings_filled.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1]
KEY_PATH = root / "paper" / "human_eval" / "key_DO_NOT_SHARE.json"
OUT_PATH = root / "artifacts" / "evaluation" / "human_eval_summary.json"

DIMS = ["faithfulness", "usefulness", "technical_correctness"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ratings_csv",
        type=Path,
        help="Filled ratings CSV (same columns as ratings_template.csv)",
    )
    parser.add_argument("--key", type=Path, default=KEY_PATH)
    args = parser.parse_args()

    key = json.loads(args.key.read_text(encoding="utf-8"))
    mapping = key["items"]  # qid -> {A: method, ...}

    rows = list(csv.DictReader(args.ratings_csv.open(encoding="utf-8")))
    scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    ranks: dict[str, list[float]] = defaultdict(list)

    used = 0
    for r in rows:
        qid = r["question_id"].strip()
        lab = r["answer_label"].strip().upper()
        if qid not in mapping or lab not in mapping[qid]:
            continue
        method = mapping[qid][lab]
        for dim in DIMS:
            val = (r.get(dim) or "").strip()
            if not val:
                continue
            scores[method][dim].append(float(val))
            used += 1
        rank = (r.get("rank") or "").strip()
        if rank:
            ranks[method].append(float(rank))

    summary = {"n_score_cells": used, "methods": {}, "mean_rank": {}}
    for method, dims in scores.items():
        summary["methods"][method] = {
            dim: {
                "n": len(vals),
                "mean": statistics.mean(vals) if vals else None,
                "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
            }
            for dim, vals in dims.items()
        }
        # overall = mean of dimension means
        means = [
            summary["methods"][method][d]["mean"]
            for d in DIMS
            if summary["methods"][method][d]["mean"] is not None
        ]
        summary["methods"][method]["overall_mean"] = (
            statistics.mean(means) if means else None
        )

    for method, vals in ranks.items():
        summary["mean_rank"][method] = {
            "n": len(vals),
            "mean": statistics.mean(vals) if vals else None,
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Saved", OUT_PATH)


if __name__ == "__main__":
    main()
