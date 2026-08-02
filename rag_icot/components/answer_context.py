"""Select a compact, facet-balanced evidence set for final answering.

ICOT accumulates many docs across iterations; dumping all of them into the
generator hurts reliability. This module keeps a small top set per needed
facet (plus exact CVE hits).
"""

from __future__ import annotations

import re
from typing import Any

from rag_icot.components.document_text import extract_cves
from rag_icot.constants.evidence_facets import EVIDENCE_FACETS


def document_facets(doc: dict[str, Any]) -> set[str]:
    meta = doc.get("metadata") or {}
    source = meta.get("source")
    doc_type = meta.get("document_type")
    facets: set[str] = set()

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

    return facets


def infer_needed_facets(
    question: str,
    covered_facets: list[str] | None = None,
    required_facets: list[str] | None = None,
) -> list[str]:
    """Infer which evidence facets the question actually needs."""

    if required_facets:
        return [f for f in required_facets if f in EVIDENCE_FACETS]

    q = (question or "").lower()
    needed: list[str] = []

    def add(facet: str) -> None:
        if facet not in needed:
            needed.append(facet)

    if re.search(r"\bcve-\d{4}-\d+\b", q) or "vulnerab" in q:
        add("vulnerability")
    if "exploit" in q or "poc" in q or "proof of concept" in q:
        add("exploit")
    if any(
        w in q
        for w in (
            "behaviour",
            "behavior",
            "malware",
            "botnet",
            "mirai",
            "iot-23",
            "traffic",
            "ddos",
        )
    ):
        add("behaviour")
    if any(
        w in q
        for w in ("mitre", "att&ck", "technique", "tactic", "map")
    ):
        add("technique")
    if any(
        w in q
        for w in ("mitigation", "mitigate", "defend", "prevention", "hardening")
    ):
        add("mitigation")

    if not needed and covered_facets:
        needed = [f for f in covered_facets if f in EVIDENCE_FACETS]

    if not needed:
        needed = ["behaviour", "vulnerability"]

    return needed


def _token_overlap(question: str, doc: dict[str, Any]) -> float:
    q_tokens = set(re.findall(r"[a-z0-9_-]{3,}", (question or "").lower()))
    if not q_tokens:
        return 0.0
    meta = doc.get("metadata") or {}
    blob = " ".join(
        [
            doc.get("text") or "",
            str(meta.get("title") or ""),
            str(meta.get("name") or ""),
            str(meta.get("cve") or ""),
            str(meta.get("malware_family") or ""),
            str(meta.get("scenario") or ""),
        ]
    ).lower()
    d_tokens = set(re.findall(r"[a-z0-9_-]{3,}", blob))
    if not d_tokens:
        return 0.0
    return len(q_tokens & d_tokens) / len(q_tokens)


def _doc_score(doc: dict[str, Any], question: str, facet: str, rank: int) -> float:
    """Higher is better. Prefer early retrieval rank + query overlap + CVE hit."""

    score = 0.0
    facets = document_facets(doc)
    if facet in facets:
        score += 2.0
    score += _token_overlap(question, doc) * 3.0

    # Prefer documents retrieved earlier (usually the initial broad hit)
    score += max(0.0, 1.5 - 0.05 * rank)

    q_cves = set(extract_cves(question))
    if q_cves:
        meta = doc.get("metadata") or {}
        doc_cve = str(meta.get("cve") or "").upper()
        text = (doc.get("text") or "").upper()
        if any(cve == doc_cve or cve in text for cve in q_cves):
            score += 5.0

    return score


def select_answer_documents(
    documents: list[dict[str, Any]],
    question: str,
    covered_facets: list[str] | None = None,
    required_facets: list[str] | None = None,
    max_per_facet: int = 2,
    max_total: int = 6,
) -> list[dict[str, Any]]:
    """Pick a compact facet-balanced subset for the answer generator."""

    if not documents:
        return []

    needed = infer_needed_facets(
        question,
        covered_facets=covered_facets,
        required_facets=required_facets,
    )

    # Always surface exact CVE matches first
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    q_cves = set(extract_cves(question))
    if q_cves:
        for doc in documents:
            meta = doc.get("metadata") or {}
            doc_cve = str(meta.get("cve") or "").upper()
            text = (doc.get("text") or "").upper()
            if any(cve == doc_cve or cve in text for cve in q_cves):
                doc_id = doc.get("id")
                if doc_id not in selected_ids:
                    selected.append(doc)
                    selected_ids.add(doc_id)
                if len(selected) >= max_per_facet:
                    break

    for facet in needed:
        ranked = sorted(
            enumerate(documents),
            key=lambda pair: _doc_score(pair[1], question, facet, pair[0]),
            reverse=True,
        )
        taken = 0
        for _, doc in ranked:
            doc_id = doc.get("id")
            if doc_id in selected_ids:
                continue
            if facet not in document_facets(doc):
                continue
            selected.append(doc)
            selected_ids.add(doc_id)
            taken += 1
            if taken >= max_per_facet or len(selected) >= max_total:
                break
        if len(selected) >= max_total:
            break

    # If still short, fill with best overall overlap
    if len(selected) < max_total:
        ranked = sorted(
            enumerate(documents),
            key=lambda pair: _doc_score(
                pair[1], question, needed[0] if needed else "behaviour", pair[0]
            ),
            reverse=True,
        )
        for _, doc in ranked:
            doc_id = doc.get("id")
            if doc_id in selected_ids:
                continue
            selected.append(doc)
            selected_ids.add(doc_id)
            if len(selected) >= max_total:
                break

    return selected[:max_total]
