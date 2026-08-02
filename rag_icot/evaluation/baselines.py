"""Baseline runners for evaluation notebooks.

All baselines reuse existing modules so experiments stay comparable.
"""

from __future__ import annotations

from typing import Any

from rag_icot.components.answer_generator import AnswerGenerator
from rag_icot.components.prompt_only_icot import PromptOnlyICOT
from rag_icot.components.retriever import Retriever
from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline
from rag_icot.evaluation.metrics import (
    compute_facet_coverage,
    source_diversity,
)


def _pack_docs(ids, documents, metadatas, distances=None) -> list[dict[str, Any]]:
    docs = []
    distances = distances or [None] * len(ids)
    for doc_id, text, meta, dist in zip(ids, documents, metadatas, distances):
        item = {
            "id": doc_id,
            "text": text,
            "metadata": meta or {},
        }
        if dist is not None:
            item["distance"] = dist
        docs.append(item)
    return docs


def run_vanilla_rag(
    question: str,
    k: int = 5,
    retriever: Retriever | None = None,
    generator: AnswerGenerator | None = None,
) -> dict[str, Any]:
    """Single-shot retrieve-then-generate (no iteration)."""

    retriever = retriever or Retriever()
    generator = generator or AnswerGenerator()

    results = retriever.retrieve(question, k=k)
    documents = _pack_docs(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        distances=(results.get("distances") or [[]])[0],
    )

    answer = generator.generate(question, documents)

    return {
        "baseline": "vanilla_rag",
        "question": question,
        "answer": answer,
        "documents": documents,
        "trace": [],
        "iterations": 1,
        "covered_facets": compute_facet_coverage(documents),
        "sources": source_diversity(documents),
    }


def run_chatiot_style(
    question: str,
    k_per_source: int = 3,
    max_docs: int = 8,
    retriever: Retriever | None = None,
    generator: AnswerGenerator | None = None,
) -> dict[str, Any]:
    """ChatIoT-like single-pass multi-retriever baseline.

    Retrieves separately from each KB source (MITRE, VARIoT, IoT23), merges
    and deduplicates by distance, then generates once. No iterative
    re-retrieve and no facet sufficiency loop (contrast with facet ICOT).
    """

    from rag_icot.constants.evidence_facets import VALID_SOURCES

    retriever = retriever or Retriever()
    generator = generator or AnswerGenerator()

    merged: dict[str, dict[str, Any]] = {}
    per_source: dict[str, int] = {}

    for source in VALID_SOURCES:
        results = retriever.retrieve(question, k=k_per_source, source=source)
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = (results.get("distances") or [[]])[0]
        per_source[source] = len(ids)
        for doc_id, text, meta, dist in zip(ids, docs, metas, dists):
            prev = merged.get(doc_id)
            if prev is None or float(dist) < float(prev.get("distance", 1e9)):
                merged[doc_id] = {
                    "id": doc_id,
                    "text": text,
                    "metadata": meta or {},
                    "distance": float(dist) if dist is not None else 1e9,
                }

    ranked = sorted(merged.values(), key=lambda d: d["distance"])[:max_docs]
    documents = [
        {"id": d["id"], "text": d["text"], "metadata": d["metadata"]}
        for d in ranked
    ]

    answer = generator.generate(question, documents)

    return {
        "baseline": "chatiot_style",
        "question": question,
        "answer": answer,
        "documents": documents,
        "trace": [
            {
                "step": "multi_source_retrieve",
                "k_per_source": k_per_source,
                "per_source_hits": per_source,
                "merged_docs": len(documents),
            }
        ],
        "iterations": 1,
        "covered_facets": compute_facet_coverage(documents),
        "sources": source_diversity(documents),
    }


def run_single_pass_rag(
    question: str,
    k: int = 5,
    retriever: Retriever | None = None,
    generator: AnswerGenerator | None = None,
) -> dict[str, Any]:
    """Alias kept for notebooks; prefer run_chatiot_style for the paper baseline."""

    return run_vanilla_rag(
        question,
        k=k,
        retriever=retriever,
        generator=generator,
    )


def run_facet_icot(
    question: str,
    max_iterations: int = 3,
    pipeline: RAGICOTPipeline | None = None,
    required_facets: list[str] | None = None,
    filter_answer_context: bool = True,
) -> dict[str, Any]:
    """Full facet-aware ICOT-RAG pipeline."""

    pipeline = pipeline or RAGICOTPipeline()
    result = pipeline.run(
        question,
        max_iterations=max_iterations,
        required_facets=required_facets,
        filter_answer_context=filter_answer_context,
    )

    documents = result["documents"]
    answer_documents = result.get("answer_documents", documents)

    return {
        "baseline": "facet_icot",
        "question": question,
        "answer": result["answer"],
        "documents": documents,
        "answer_documents": answer_documents,
        "trace": result["trace"],
        "iterations": len(result["trace"]),
        "covered_facets": result.get(
            "covered_facets",
            compute_facet_coverage(documents),
        ),
        "sources": source_diversity(documents),
    }


def run_prompt_only_icot(
    question: str,
    llm=None,
) -> dict[str, Any]:
    """Zeng-style prompt-only ICoT baseline (no retrieval).

    Multi-stage role + chain-of-thought + advice, without a knowledge base.
    Retrieval metrics are empty by design (documents=[]).
    """

    runner = PromptOnlyICOT(llm=llm)
    result = runner.run(question)

    return {
        "baseline": "prompt_only_icot",
        "question": question,
        "answer": result["answer"],
        "documents": [],
        "answer_documents": [],
        "trace": result["trace"],
        "iterations": len(result["trace"]),
        "covered_facets": [],
        "sources": {},
        "analysis": result.get("analysis", ""),
        "expansion": result.get("expansion", ""),
    }


def run_prompt_only_icot_stub(question: str) -> dict[str, Any]:
    """Backward-compatible alias for run_prompt_only_icot."""

    return run_prompt_only_icot(question)
