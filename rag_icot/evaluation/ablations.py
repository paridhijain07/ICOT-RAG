"""Ablation configs and helpers for ICOT-RAG experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from rag_icot.components.retriever import Retriever
from rag_icot.evaluation.baselines import (
    run_facet_icot,
    run_prompt_only_icot,
    run_vanilla_rag,
)
from rag_icot.evaluation.metrics import (
    compute_facet_coverage,
    facet_recall,
    source_diversity,
    summarize_run,
)


@dataclass(frozen=True)
class AblationConfig:
    id: str
    name: str
    description: str
    needs_llm: bool
    params: dict[str, Any]


# Retrieval-only ablations (safe while Gemini quota is exhausted)
RETRIEVAL_ABLATIONS = [
    AblationConfig(
        id="ret_baseline_k5",
        name="Single-pass k=5",
        description="Default single retrieval, k=5, no source filter",
        needs_llm=False,
        params={"k": 5, "source": None, "facet": None},
    ),
    AblationConfig(
        id="ret_k10",
        name="Single-pass k=10",
        description="Larger single retrieval window",
        needs_llm=False,
        params={"k": 10, "source": None, "facet": None},
    ),
    AblationConfig(
        id="ret_source_iot23",
        name="Forced IoT23",
        description="Retrieve only from IoT23",
        needs_llm=False,
        params={"k": 5, "source": "IoT23", "facet": None},
    ),
    AblationConfig(
        id="ret_source_mitre",
        name="Forced MITRE",
        description="Retrieve only from MITRE",
        needs_llm=False,
        params={"k": 5, "source": "MITRE", "facet": None},
    ),
    AblationConfig(
        id="ret_source_variot",
        name="Forced VARIoT",
        description="Retrieve only from VARIoT",
        needs_llm=False,
        params={"k": 5, "source": "VARIoT", "facet": None},
    ),
    AblationConfig(
        id="ret_facet_behaviour",
        name="Facet=behaviour",
        description="Facet-filtered retrieval for behaviour",
        needs_llm=False,
        params={"k": 5, "source": None, "facet": "behaviour"},
    ),
    AblationConfig(
        id="ret_facet_vulnerability",
        name="Facet=vulnerability",
        description="Facet-filtered retrieval for vulnerability",
        needs_llm=False,
        params={"k": 5, "source": None, "facet": "vulnerability"},
    ),
]


# LLM ablations (run after Gemini quota resets)
LLM_ABLATIONS = [
    AblationConfig(
        id="llm_vanilla",
        name="Vanilla RAG",
        description="Single retrieve + generate",
        needs_llm=True,
        params={"mode": "vanilla", "max_iterations": 1},
    ),
    AblationConfig(
        id="llm_prompt_only_icot",
        name="Prompt-only ICoT (Zeng-style)",
        description="Role + multi-stage CoT advice with no retrieval",
        needs_llm=True,
        params={"mode": "prompt_only_icot", "max_iterations": 3},
    ),
    AblationConfig(
        id="llm_icot_iter1",
        name="Facet ICOT max_iter=1",
        description="Facet loop capped at 1 iteration",
        needs_llm=True,
        params={"mode": "facet_icot", "max_iterations": 1},
    ),
    AblationConfig(
        id="llm_icot_iter3",
        name="Facet ICOT max_iter=3",
        description="Full facet-aware iterative loop",
        needs_llm=True,
        params={"mode": "facet_icot", "max_iterations": 3},
    ),
]


def run_retrieval_ablation(
    question: str,
    required_facets: list[str],
    config: AblationConfig,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Run one retrieval-only ablation for a question."""

    if config.needs_llm:
        raise ValueError(f"{config.id} requires LLM; use LLM ablation runner later")

    retriever = retriever or Retriever()
    params = config.params

    results = retriever.retrieve(
        question,
        k=params.get("k", 5),
        source=params.get("source"),
        facet=params.get("facet"),
    )

    documents = [
        {
            "id": doc_id,
            "text": text,
            "metadata": meta or {},
        }
        for doc_id, text, meta in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        )
    ]

    covered = compute_facet_coverage(documents)

    return {
        "ablation_id": config.id,
        "ablation_name": config.name,
        "question": question,
        "required_facets": required_facets,
        "covered_facets": covered,
        "facet_recall": facet_recall(required_facets, covered),
        "sources": source_diversity(documents),
        "doc_count": len(documents),
        "top_ids": [d["id"] for d in documents],
        "params": params,
    }


def summarize_ablation_table(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate mean facet recall per ablation id."""

    from collections import defaultdict

    bucket: dict[str, list[float]] = defaultdict(list)
    names: dict[str, str] = {}

    for row in rows:
        aid = row["ablation_id"]
        bucket[aid].append(row["facet_recall"])
        names[aid] = row["ablation_name"]

    summary = []
    for aid, scores in bucket.items():
        summary.append(
            {
                "ablation_id": aid,
                "ablation_name": names[aid],
                "n": len(scores),
                "mean_facet_recall": sum(scores) / len(scores),
            }
        )

    summary.sort(key=lambda x: x["mean_facet_recall"], reverse=True)
    return summary


def run_llm_ablation(
    question: str,
    config: AblationConfig,
    required_facets: list[str] | None = None,
    expected_sources: list[str] | None = None,
    reference_hints: list[str] | None = None,
    retriever=None,
    generator=None,
    pipeline=None,
) -> dict[str, Any]:
    """Run one LLM ablation (vanilla or facet ICOT with max_iterations)."""

    if not config.needs_llm:
        raise ValueError(f"{config.id} is retrieval-only; use run_retrieval_ablation")

    mode = config.params.get("mode", "vanilla")
    max_iterations = int(config.params.get("max_iterations", 1))

    if mode == "vanilla":
        run = run_vanilla_rag(
            question,
            k=5,
            retriever=retriever,
            generator=generator,
        )
    elif mode == "prompt_only_icot":
        llm = getattr(generator, "llm", None) if generator is not None else None
        run = run_prompt_only_icot(question, llm=llm)
    elif mode == "facet_icot":
        run = run_facet_icot(
            question,
            max_iterations=max_iterations,
            pipeline=pipeline,
            required_facets=required_facets,
            filter_answer_context=True,
        )
    else:
        raise ValueError(f"Unknown LLM ablation mode: {mode}")

    summary = summarize_run(
        run,
        required_facets=required_facets,
        expected_sources=expected_sources,
        reference_hints=reference_hints,
    )

    return {
        "ablation_id": config.id,
        "ablation_name": config.name,
        "question": question,
        "answer": run.get("answer", ""),
        "documents": run.get("documents", []),
        "answer_documents": run.get("answer_documents", run.get("documents", [])),
        "trace": run.get("trace", []),
        **summary,
        "params": config.params,
    }
