"""Scaled ablations on all multi-facet questions (resume + rate-limit safe).

1) Iteration budget: vanilla vs ICOT max_iter=1 vs max_iter=3
2) Answer-context filter: same retrieval, full vs filtered generation

Examples:
  python scripts/run_scaled_ablations.py
  python scripts/run_scaled_ablations.py --only iter
  python scripts/run_scaled_ablations.py --only filter --resume
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from rag_icot.components.answer_context import select_answer_documents
from rag_icot.components.context_format import format_documents_for_llm
from rag_icot.evaluation import (
    LLM_ABLATIONS,
    AnswerJudge,
    load_eval_dataset,
    run_llm_ablation,
    summarize_run,
)
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

PAUSE = 6
OUT_DIR = root / "artifacts" / "evaluation"
ITER_OUT = OUT_DIR / "llm_iter_ablation_multifacet.json"
FILTER_OUT = OUT_DIR / "answer_context_filter_multifacet.json"
ITER_CONFIGS = [
    c
    for c in LLM_ABLATIONS
    if c.id in {"llm_vanilla", "llm_icot_iter1", "llm_icot_iter3"}
]


def _is_rate_limit(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    return (
        "ratelimit" in name
        or "rate_limit" in msg
        or "rate limit" in msg
        or "429" in msg
        or "tokens per day" in msg
    )


def _rate_limit_sleep_seconds(exc: BaseException, fallback: float = 180.0) -> float:
    msg = str(exc)
    m = re.search(
        r"try again in\s+(?:(\d+)m)?\s*([\d.]+)s",
        msg,
        flags=re.IGNORECASE,
    )
    if not m:
        return fallback
    minutes = int(m.group(1) or 0)
    seconds = float(m.group(2) or 0)
    return max(fallback, minutes * 60 + seconds + 5)


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _preview(docs: list) -> str:
    return format_documents_for_llm(docs, max_docs=5, max_chars=400)


def _iter_summary(rows: list[dict]) -> dict:
    agg: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for aid, payload in row.get("ablations", {}).items():
            agg[aid]["facet_recall"].append(payload["facet_recall"])
            agg[aid]["keyword_hit_rate"].append(payload["keyword_hit_rate"])
            agg[aid]["source_hit_rate"].append(payload["source_hit_rate"])
            agg[aid]["judge_overall"].append(payload["judge"]["overall"])
    return {
        aid: {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}
        | {"n": len(next(iter(metrics.values()), []))}
        for aid, metrics in agg.items()
    }


def _filter_summary(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {"n": 0}
    avg_full = sum(r["judges"]["full_context"]["overall"] for r in rows) / n
    avg_filt = sum(r["judges"]["filtered"]["overall"] for r in rows) / n
    return {
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
        "avg_retrieved_docs": sum(r["retrieved_docs"] for r in rows) / n,
        "avg_filtered_docs": sum(r["filtered_answer_docs"] for r in rows) / n,
    }


def run_iter(
    questions: list,
    pipeline,
    judge,
    resume: bool,
    pause: float,
    max_retries: int,
) -> None:
    rows: list[dict] = []
    errors: list[dict] = []
    done: set[str] = set()
    if resume and ITER_OUT.exists():
        prev = json.loads(ITER_OUT.read_text(encoding="utf-8"))
        rows = list(prev.get("rows") or [])
        done = {r["id"] for r in rows}
        errors = [e for e in (prev.get("errors") or []) if e.get("id") in done]
        print(f"Iter resume: {len(done)} done", flush=True)

    retriever = pipeline.engine.retriever
    generator = pipeline.generator

    for q in questions:
        if q.id in done:
            continue
        print("\n" + "=" * 80, flush=True)
        print("ITER", q.id, q.required_facets, flush=True)
        print(q.question, flush=True)

        attempt = 0
        while True:
            attempt += 1
            try:
                q_row = {
                    "id": q.id,
                    "category": q.category,
                    "question": q.question,
                    "required_facets": q.required_facets,
                    "ablations": {},
                }
                for cfg in ITER_CONFIGS:
                    print(f"  -> {cfg.id}", flush=True)
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
                    docs = result.get("answer_documents") or result["documents"]
                    j = judge.score(
                        question=q.question,
                        answer=result["answer"],
                        gold_notes=q.gold_notes,
                        reference_hints=q.reference_hints,
                        evidence_preview=_preview(docs),
                    )
                    q_row["ablations"][cfg.id] = {
                        "ablation_name": cfg.name,
                        "facet_recall": result["facet_recall"],
                        "keyword_hit_rate": result["keyword_hit_rate"],
                        "source_hit_rate": result["source_hit_rate"],
                        "iterations": result["iterations"],
                        "doc_count": result["doc_count"],
                        "answer_doc_count": len(docs),
                        "sources": result["sources"],
                        "judge": j,
                        "answer_preview": result["answer"][:400],
                    }
                    print(
                        f"     fac={result['facet_recall']:.2f} "
                        f"src={result['source_hit_rate']:.2f} "
                        f"judge={j['overall']:.2f}",
                        flush=True,
                    )
                    time.sleep(2)
                rows.append(q_row)
                done.add(q.id)
                break
            except Exception as exc:
                if _is_rate_limit(exc) and attempt <= max_retries:
                    wait = _rate_limit_sleep_seconds(exc)
                    print(
                        f"RATE LIMIT {q.id} attempt {attempt}/{max_retries}; "
                        f"sleep {wait:.0f}s",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                print(f"FAILED ITER {q.id}: {type(exc).__name__}: {exc}", flush=True)
                errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})
                break

        payload = {
            "config": {
                "category": "multi_facet",
                "answer_context_filtered": True,
                "ablations": [c.id for c in ITER_CONFIGS],
                "n_target": len(questions),
                "llm_provider": generator.llm.provider,
                "llm_model": generator.llm.model_name,
            },
            "rows": rows,
            "errors": errors,
            "summary": _iter_summary(rows),
        }
        _save(ITER_OUT, payload)
        print(f"Saved {ITER_OUT} rows={len(rows)}", flush=True)
        time.sleep(pause)

    print("ITER SUMMARY", json.dumps(_iter_summary(rows), indent=2), flush=True)


def run_filter(
    questions: list,
    pipeline,
    judge,
    resume: bool,
    pause: float,
    max_retries: int,
) -> None:
    rows: list[dict] = []
    errors: list[dict] = []
    done: set[str] = set()
    if resume and FILTER_OUT.exists():
        prev = json.loads(FILTER_OUT.read_text(encoding="utf-8"))
        rows = list(prev.get("rows") or [])
        done = {r["id"] for r in rows}
        errors = [e for e in (prev.get("errors") or []) if e.get("id") in done]
        print(f"Filter resume: {len(done)} done", flush=True)

    for q in questions:
        if q.id in done:
            continue
        print("\n" + "=" * 80, flush=True)
        print("FILTER", q.id, flush=True)
        print(q.question, flush=True)

        attempt = 0
        while True:
            attempt += 1
            try:
                reasoned = pipeline.engine.reason(
                    q.question,
                    max_iterations=3,
                )
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
                    f"retrieved={len(all_docs)} filtered={len(filtered_docs)}",
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
                    evidence_preview=_preview(all_docs),
                )
                time.sleep(2)
                j_filt = judge.score(
                    q.question,
                    ans_filt,
                    gold_notes=q.gold_notes,
                    reference_hints=q.reference_hints,
                    evidence_preview=_preview(filtered_docs),
                )
                hard_full = summarize_run(
                    {
                        "documents": all_docs,
                        "answer": ans_full,
                        "covered_facets": covered,
                    },
                    required_facets=q.required_facets,
                    expected_sources=q.expected_sources,
                    reference_hints=q.reference_hints,
                )
                print(
                    f"judge full={j_full['overall']:.2f} "
                    f"filtered={j_filt['overall']:.2f} "
                    f"delta={j_filt['overall'] - j_full['overall']:+.2f}",
                    flush=True,
                )
                rows.append(
                    {
                        "id": q.id,
                        "category": q.category,
                        "required_facets": q.required_facets,
                        "retrieved_docs": len(all_docs),
                        "filtered_answer_docs": len(filtered_docs),
                        "filtered_ids": [d["id"] for d in filtered_docs],
                        "retrieval": hard_full,
                        "judges": {"full_context": j_full, "filtered": j_filt},
                        "full_preview": ans_full[:350],
                        "filtered_preview": ans_filt[:350],
                    }
                )
                done.add(q.id)
                break
            except Exception as exc:
                if _is_rate_limit(exc) and attempt <= max_retries:
                    wait = _rate_limit_sleep_seconds(exc)
                    print(
                        f"RATE LIMIT {q.id} attempt {attempt}/{max_retries}; "
                        f"sleep {wait:.0f}s",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                print(f"FAILED FILTER {q.id}: {type(exc).__name__}: {exc}", flush=True)
                errors.append({"id": q.id, "error": f"{type(exc).__name__}: {exc}"})
                break

        payload = {
            "config": {
                "category": "multi_facet",
                "icot_max_iterations": 3,
                "max_per_facet": 2,
                "max_total": 6,
                "n_target": len(questions),
                "llm_provider": pipeline.generator.llm.provider,
                "llm_model": pipeline.generator.llm.model_name,
            },
            "rows": rows,
            "errors": errors,
            "summary": _filter_summary(rows),
        }
        _save(FILTER_OUT, payload)
        print(f"Saved {FILTER_OUT} rows={len(rows)}", flush=True)
        time.sleep(pause)

    print("FILTER SUMMARY", json.dumps(_filter_summary(rows), indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["all", "iter", "filter"], default="all")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pause", type=float, default=PAUSE)
    parser.add_argument("--max-retries", type=int, default=8)
    args = parser.parse_args()

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
    judge = AnswerJudge(llm=pipeline.generator.llm)
    print(
        "LLM",
        pipeline.generator.llm.provider,
        pipeline.generator.llm.model_name,
        flush=True,
    )

    if args.only in {"all", "iter"}:
        run_iter(
            questions,
            pipeline,
            judge,
            resume=args.resume,
            pause=args.pause,
            max_retries=args.max_retries,
        )
    if args.only in {"all", "filter"}:
        run_filter(
            questions,
            pipeline,
            judge,
            resume=args.resume,
            pause=args.pause,
            max_retries=args.max_retries,
        )
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
