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


def _pack_docs(ids, documents, metadatas) -> list[dict[str, Any]]:
    docs = []
    for doc_id, text, meta in zip(ids, documents, metadatas):
        docs.append(
            {
                "id": doc_id,
                "text": text,
                "metadata": meta or {},
            }
        )
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


def run_single_pass_rag(
    question: str,
    k: int = 5,
    retriever: Retriever | None = None,
    generator: AnswerGenerator | None = None,
) -> dict[str, Any]:
    """ChatIoT-like single pass: retrieve once from mixed index, generate.

    (No selector yet; uses the same unified collection.)
    """

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
