"""Build consistent embeddable / retrievable text for KB documents.

Dense retrieval fails when identifiers (CVE IDs, malware names) are buried
deep in long descriptions. This module front-loads those signals.
"""

from __future__ import annotations

import re
from typing import Any


_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)

# Pull product phrases from advisory prose when structured fields are empty.
_PRODUCT_PATTERNS = [
    re.compile(
        r"affected installations of ([^.]+?)(?:\.| with firmware)",
        re.IGNORECASE,
    ),
    re.compile(
        r"installations of ([^.]+?)(?:\.| with firmware)",
        re.IGNORECASE,
    ),
    re.compile(
        r"affects? ([A-Z][^.]{5,160}?)(?:\.|$)",
    ),
]


def extract_cves(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for match in _CVE_RE.findall(text):
            cve = match.upper()
            if cve not in seen:
                seen.add(cve)
                found.append(cve)
    return found


def extract_products_from_text(*texts: str) -> list[str]:
    products: list[str] = []
    seen: set[str] = set()

    for text in texts:
        if not text:
            continue
        for pattern in _PRODUCT_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            raw = match.group(1).strip()
            raw = re.sub(r"\s+", " ", raw)
            # Split common list phrasing
            parts = re.split(r",| and ", raw)
            for part in parts:
                item = part.strip(" .;")
                item = re.sub(
                    r"\s+(routers?|devices?|firmware)\s*$",
                    "",
                    item,
                    flags=re.IGNORECASE,
                ).strip()
                if len(item) < 3:
                    continue
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                products.append(item)

    return products[:12]


def _as_product_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        return [value] if value and value not in {"[]", "None"} else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = (
                    item.get("name")
                    or item.get("product")
                    or item.get("data")
                    or ""
                )
                name = str(name).strip()
                if name:
                    out.append(name)
            else:
                name = str(item).strip()
                if name and name not in {"[]", "None"}:
                    out.append(name)
        return out
    return []


def enrich_variot_products(doc: dict[str, Any]) -> list[str]:
    """Return products from metadata or heuristic parse of title/description."""

    products = _as_product_list(doc.get("affected_products"))
    if products:
        return products
    return extract_products_from_text(
        doc.get("title") or "",
        doc.get("description") or "",
    )


def _strip_leading_title(body: str, title: str) -> str:
    if not body or not title:
        return body or ""
    if body.startswith(title):
        return body[len(title) :].strip(" -:|\n")
    return body


def build_document_text(doc: dict[str, Any]) -> str:
    """Single source of truth for embedding + Chroma document text."""

    source = (doc.get("source") or "").upper()
    doc_type = doc.get("document_type") or ""

    if source == "VARIOT" or doc_type in {"vulnerability", "exploit"}:
        return _variot_text(doc)

    if source == "IOT23":
        return _iot23_text(doc)

    if source == "MITRE":
        return _mitre_text(doc)

    return (
        doc.get("description")
        or doc.get("summary")
        or doc.get("title")
        or doc.get("name")
        or ""
    )


def _variot_text(doc: dict[str, Any]) -> str:
    title = (doc.get("title") or "").strip()
    body = _strip_leading_title(doc.get("description") or "", title)

    cves = []
    if doc.get("cve"):
        cves = [str(doc["cve"]).strip().upper()]
    if not cves:
        cves = extract_cves(title, body)

    products = enrich_variot_products(
        {
            **doc,
            "title": title,
            "description": body,
        }
    )

    parts: list[str] = []
    if cves:
        parts.append("CVE: " + ", ".join(cves))
    if title:
        parts.append(f"Title: {title}")
    if products:
        parts.append("Affected products: " + ", ".join(products))
    if body:
        parts.append(body)

    return "\n".join(parts).strip()


def _iot23_text(doc: dict[str, Any]) -> str:
    family = doc.get("malware_family") or doc.get("attack_type") or ""
    scenario = doc.get("scenario") or ""
    title = doc.get("title") or ""
    summary = doc.get("summary") or doc.get("description") or ""
    behaviours = doc.get("behaviours") or {}
    scenarios = doc.get("scenarios") or []

    parts = []
    if family:
        parts.append(f"Malware family: {family}")
    if scenario:
        parts.append(f"Scenario: {scenario}")
    if scenarios and not scenario:
        parts.append(f"Scenarios: {', '.join(str(s) for s in scenarios)}")
    if title and title not in summary:
        parts.append(f"Title: {title}")
    if behaviours:
        top = ", ".join(
            f"{label} ({count})"
            for label, count in sorted(
                behaviours.items(),
                key=lambda item: int(item[1]),
                reverse=True,
            )[:8]
        )
        parts.append(f"Observed behaviours: {top}")
    if summary:
        parts.append(summary)

    return "\n".join(parts).strip()


def _mitre_text(doc: dict[str, Any]) -> str:
    tid = doc.get("technique_id") or ""
    name = doc.get("name") or ""
    description = doc.get("description") or ""

    parts = []
    if tid:
        parts.append(f"MITRE ATT&CK technique {tid}")
    if name:
        parts.append(name)
    if description:
        parts.append(description)

    return "\n".join(parts).strip()
