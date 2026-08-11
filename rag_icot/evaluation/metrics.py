from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any


def compute_facet_coverage(documents: list[dict[str, Any]]) -> list[str]:
    """Infer facets from retrieved document metadata."""

    facets = set()

    for doc in documents:
        meta = doc.get("metadata") or {}
        source = meta.get("source")
        doc_type = meta.get("document_type")

        if source == "IoT23":
            facets.add("behaviour")
        elif source == "MITRE":
            facets.add("technique")
            facets.add("mitigation")
        elif source == "VARIoT":
            if doc_type == "exploit":
                facets.add("exploit")
            else:
                facets.add("vulnerability")

    return sorted(facets)


def source_diversity(documents: list[dict[str, Any]]) -> dict[str, int]:
    return dict(
        Counter(
            (doc.get("metadata") or {}).get("source", "unknown")
            for doc in documents
        )
    )


def facet_recall(
    required_facets: list[str],
    covered_facets: list[str],
) -> float:
    if not required_facets:
        return 1.0

    covered = set(covered_facets)
    hit = sum(1 for f in required_facets if f in covered)
    return hit / len(required_facets)


def documents_blob(documents: list[dict[str, Any]]) -> str:
    """Flatten retrieved docs for cheap string matching."""

    parts: list[str] = []
    for doc in documents:
        parts.append(doc.get("text") or "")
        parts.append(json.dumps(doc.get("metadata") or {}, ensure_ascii=False))
    return "\n".join(parts)


def keyword_hits(
    documents: list[dict[str, Any]],
    hints: list[str] | None = None,
) -> dict[str, Any]:
    """Check whether gold reference hints appear in retrieved evidence."""

    hints = [h for h in (hints or []) if str(h).strip()]
    if not hints:
        return {
            "hints": [],
            "matched_hints": [],
            "keyword_hit": True,
            "keyword_hit_rate": 1.0,
        }

    blob = documents_blob(documents).lower()
    matched = [h for h in hints if str(h).lower() in blob]
    rate = len(matched) / len(hints)

    return {
        "hints": hints,
        "matched_hints": matched,
        "keyword_hit": rate > 0.0,
        "keyword_hit_rate": rate,
    }


def source_hits(
    documents: list[dict[str, Any]],
    expected_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Fraction of expected KB sources present in the retrieved set."""

    expected = [s for s in (expected_sources or []) if str(s).strip()]
    present = {
        (doc.get("metadata") or {}).get("source")
        for doc in documents
        if (doc.get("metadata") or {}).get("source")
    }

    if not expected:
        return {
            "expected_sources": [],
            "matched_sources": sorted(present),
            "source_hit": True,
            "source_hit_rate": 1.0,
        }

    matched = [s for s in expected if s in present]
    rate = len(matched) / len(expected)

    return {
        "expected_sources": expected,
        "matched_sources": matched,
        "source_hit": rate > 0.0,
        "source_hit_rate": rate,
    }


def facet_recall_at_budget(
    documents: list[dict[str, Any]],
    required_facets: list[str] | None = None,
    max_docs: int = 6,
) -> dict[str, Any]:
    """Facet recall using only the first ``max_docs`` documents."""

    budgeted = list(documents or [])[:max_docs]
    covered = compute_facet_coverage(budgeted)
    required = required_facets or []
    return {
        "budget_docs": len(budgeted),
        "max_docs": max_docs,
        "covered_facets_at_budget": covered,
        "facet_recall_at_budget": facet_recall(required, covered),
    }


def faithfulness_support(
    answer: str,
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    """Light grounding check for CVEs / ATT&CK IDs mentioned in the answer.

    Rate = supported IDs / mentioned IDs. If no IDs are mentioned, return
    1.0 when the answer admits insufficient evidence, else 0.5 (neutral).
    """

    answer_l = (answer or "").lower()
    blob = documents_blob(documents).lower()

    cves = sorted(set(re.findall(r"cve-\d{4}-\d+", answer_l)))
    techs = sorted(set(re.findall(r"\bt\d{4}(?:\.\d{3})?\b", answer_l)))

    supported: list[str] = []
    unsupported: list[str] = []
    for item in cves + techs:
        if item in blob:
            supported.append(item)
        else:
            unsupported.append(item)

    claims = len(cves) + len(techs)
    if claims == 0:
        admits = any(
            p in answer_l
            for p in (
                "insufficient",
                "not mentioned",
                "not explicitly",
                "no evidence",
                "not covered",
                "not in the provided",
                "cannot verify",
            )
        )
        rate = 1.0 if admits else 0.5
    else:
        rate = len(supported) / claims

    return {
        "faithfulness_rate": rate,
        "mentioned_ids": cves + techs,
        "supported_ids": supported,
        "unsupported_ids": unsupported,
    }


def summarize_run(
    run: dict[str, Any],
    required_facets: list[str] | None = None,
    expected_sources: list[str] | None = None,
    reference_hints: list[str] | None = None,
    budget_docs: int = 6,
) -> dict[str, Any]:
    required = required_facets or []
    documents = run.get("documents", [])
    # Prefer filtered answer docs for budgeted metrics when present
    answer_docs = run.get("answer_documents") or documents
    covered = run.get("covered_facets") or compute_facet_coverage(documents)
    kw = keyword_hits(documents, reference_hints)
    src = source_hits(documents, expected_sources)
    at_budget = facet_recall_at_budget(
        answer_docs,
        required_facets=required,
        max_docs=budget_docs,
    )
    faith = faithfulness_support(run.get("answer") or "", answer_docs)

    return {
        "baseline": run.get("baseline"),
        "iterations": run.get("iterations", 1),
        "doc_count": len(documents),
        "answer_doc_count": len(answer_docs),
        "sources": run.get("sources") or source_diversity(documents),
        "covered_facets": covered,
        "required_facets": required,
        "facet_recall": facet_recall(required, covered),
        "facet_recall_at_budget": at_budget["facet_recall_at_budget"],
        "budget_docs": at_budget["budget_docs"],
        "covered_facets_at_budget": at_budget["covered_facets_at_budget"],
        "faithfulness_rate": faith["faithfulness_rate"],
        "faithfulness_supported_ids": faith["supported_ids"],
        "faithfulness_unsupported_ids": faith["unsupported_ids"],
        "has_trace": bool(run.get("trace")),
        "keyword_hit": kw["keyword_hit"],
        "keyword_hit_rate": kw["keyword_hit_rate"],
        "matched_hints": kw["matched_hints"],
        "source_hit": src["source_hit"],
        "source_hit_rate": src["source_hit_rate"],
        "matched_sources": src["matched_sources"],
    }
