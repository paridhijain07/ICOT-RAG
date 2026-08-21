"""Free web research fallback (DuckDuckGo + existing Groq/Gemini LLM).

Used only when local KB evidence is weak. Prefer official / vendor domains
before generic web pages. Optional ingest into Chroma for demo KB growth.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

# Prefer these hosts when ranking / deciding to grow the KB.
ALLOWLIST_SUFFIXES = (
    "mitre.org",
    "nvd.nist.gov",
    "cisa.gov",
    "nist.gov",
    "microsoft.com",
    "cisco.com",
    "ibm.com",
    "redhat.com",
    "ubuntu.com",
    "debian.org",
    "apache.org",
    "owasp.org",
    "first.org",
    "cert.org",
    "sans.org",
    "variotdbs.eu",
    "stratosphereips.org",
    "github.com",
    "arxiv.org",
    "ieee.org",
    "acm.org",
)

_INSUFFICIENT_PHRASES = (
    "insufficient",
    "not mentioned",
    "not explicitly",
    "no evidence",
    "not covered",
    "not in the provided",
    "cannot verify",
    "not found in",
    "do not have evidence",
    "evidence does not",
    "unable to confirm",
)


def host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == s or host.endswith("." + s) for s in ALLOWLIST_SUFFIXES)


def kb_evidence_weak(
    *,
    answer: str,
    documents: list[dict[str, Any]],
    needed_facets: list[str] | None,
    covered_facets: list[str] | None,
) -> tuple[bool, str]:
    """Heuristic gate: True when local KB likely cannot answer well."""

    needed = list(needed_facets or [])
    covered = set(covered_facets or [])
    missing = [f for f in needed if f not in covered]
    docs = documents or []
    answer_l = (answer or "").lower()

    if not docs:
        return True, "no_retrieved_documents"

    if any(p in answer_l for p in _INSUFFICIENT_PHRASES):
        return True, "answer_admits_insufficient_evidence"

    if missing and len(docs) < 3:
        return True, f"needed_facets_still_missing:{','.join(missing)}"

    distances = [
        float(d["distance"])
        for d in docs
        if d.get("distance") is not None
    ]
    if distances:
        avg = sum(distances) / len(distances)
        # Cosine/L2-on-unit: larger = worse match. Conservative threshold.
        if avg > 1.15:
            return True, f"weak_retrieval_avg_distance={avg:.3f}"

    return False, "kb_ok"


def search_duckduckgo(query: str, max_results: int = 8) -> list[dict[str, str]]:
    """Free web search via ddgs (no API key). Tries multiple backends."""

    try:
        from ddgs import DDGS
        from ddgs.exceptions import DDGSException
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Install free search package: pip install ddgs"
        ) from exc

    raw: list[dict[str, Any]] = []
    errors: list[str] = []
    # bing/google backends via ddgs are free (no key); duckduckgo often empty
    # in some regions.
    for backend in ("bing", "google", "duckduckgo", "yahoo"):
        try:
            with DDGS() as ddgs:
                batch = list(
                    ddgs.text(query, max_results=max_results, backend=backend)
                ) or []
            if batch:
                raw = batch
                break
        except DDGSException as exc:
            errors.append(f"{backend}:{exc}")
        except Exception as exc:  # network / parse quirks
            errors.append(f"{backend}:{type(exc).__name__}")

    if not raw:
        raise RuntimeError(
            "Free web search returned no results. "
            + (" Tried: " + "; ".join(errors) if errors else "")
        )

    hits: list[dict[str, str]] = []
    for item in raw:
        url = (item.get("href") or item.get("link") or "").strip()
        title = (item.get("title") or "").strip()
        body = (item.get("body") or item.get("snippet") or "").strip()
        if not url or not (title or body):
            continue
        hits.append(
            {
                "title": title,
                "url": url,
                "snippet": body,
                "allowlisted": "1" if host_allowed(url) else "0",
            }
        )

    # Prefer allowlisted hosts, keep order otherwise.
    hits.sort(key=lambda h: (0 if h["allowlisted"] == "1" else 1))
    return hits


def _coerce_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "quality": "low",
        "summary": text[:1200],
        "key_facts": [],
        "cves": [],
        "techniques": [],
        "should_ingest": False,
        "reason": "unparseable_llm_json",
    }


def synthesize_web_note(
    question: str,
    hits: list[dict[str, str]],
    llm,
) -> dict[str, Any]:
    """LLM CoT over search snippets → structured note (free Groq/Gemini)."""

    if not hits:
        return {
            "quality": "low",
            "summary": "No web search hits.",
            "key_facts": [],
            "cves": [],
            "techniques": [],
            "should_ingest": False,
            "sources": [],
            "reason": "no_hits",
        }

    bullet = "\n".join(
        f"- [{h['allowlisted']}] {h['title']}\n  URL: {h['url']}\n  "
        f"Snippet: {h['snippet'][:400]}"
        for h in hits[:8]
    )
    prompt = f"""You are an IoT cybersecurity analyst doing careful web research.

Question:
{question}

Search hits BELOW were already retrieved by an external search API.
Do NOT call tools or browsers. Only read these hits and output JSON.

Search hits (allowlisted=1 means preferred official/vendor domain):
{bullet}

Think step by step silently, then output ONLY valid JSON with keys:
- quality: "high" | "medium" | "low"
- summary: 4-8 sentence grounded note (no invented CVEs/IDs)
- key_facts: string array
- cves: string array (only if present in snippets)
- techniques: string array (ATT&CK IDs only if present)
- should_ingest: boolean (true only if quality is high/medium AND at least one
  allowlisted=1 source supports the main claims)
- reason: short string

Rules: Do not invent identifiers. Prefer allowlisted sources. If snippets are
weak or conflicting, quality=low and should_ingest=false.
If hits are unrelated to the question, quality=low, should_ingest=false,
and say so in summary.
"""
    raw = llm.generate(prompt)
    data = _coerce_json(raw)
    data["sources"] = [
        {"title": h["title"], "url": h["url"], "allowlisted": h["allowlisted"]}
        for h in hits
    ]
    data["query"] = question
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    return data


def web_note_to_document(note: dict[str, Any]) -> dict[str, Any]:
    """Build a Chroma-ready document + answer-context doc from a web note."""

    sources = note.get("sources") or []
    urls = [s.get("url") for s in sources if s.get("url")]
    allowlisted_urls = [
        s.get("url")
        for s in sources
        if s.get("allowlisted") == "1" and s.get("url")
    ]
    digest = hashlib.sha1(
        ((note.get("query") or "") + "|" + (note.get("summary") or "")).encode(
            "utf-8"
        )
    ).hexdigest()[:12]
    doc_id = f"web_{digest}"

    facts = note.get("key_facts") or []
    cves = note.get("cves") or []
    techniques = note.get("techniques") or []
    description = "\n".join(
        [
            f"Web research note for: {note.get('query') or ''}",
            "",
            note.get("summary") or "",
            "",
            "Key facts:",
            *[f"- {f}" for f in facts],
            "",
            "CVEs: " + (", ".join(cves) if cves else "none stated"),
            "Techniques: "
            + (", ".join(techniques) if techniques else "none stated"),
            "",
            "Sources:",
            *[f"- {u}" for u in urls[:8]],
        ]
    ).strip()

    meta = {
        "source": "WEB",
        "document_type": "web_research_note",
        "title": f"Web note: {(note.get('query') or '')[:80]}",
        "quality": str(note.get("quality") or "low"),
        "created_at": str(note.get("created_at") or ""),
        "urls": " | ".join(urls[:8]),
        "allowlisted_urls": " | ".join(allowlisted_urls[:8]),
        "cve": (cves[0] if cves else ""),
        "web_grown": True,
    }

    # Flat fields for VectorStore.add_documents + embed text builder
    flat = {
        "id": doc_id,
        "source": "WEB",
        "document_type": "web_research_note",
        "title": meta["title"],
        "description": description,
        "summary": note.get("summary") or "",
        "quality": meta["quality"],
        "created_at": meta["created_at"],
        "urls": meta["urls"],
        "cve": meta["cve"],
        "web_grown": True,
    }

    answer_doc = {
        "id": doc_id,
        "text": description,
        "metadata": meta,
        "distance": 0.0,
    }
    return {"flat": flat, "answer_doc": answer_doc}


def ingest_web_document(flat_doc: dict[str, Any], retriever) -> bool:
    """Append one web note into the live Chroma collection."""

    try:
        emb = retriever.embedding_builder.embed_documents([flat_doc])
        # Ensure collection handle is set
        store = retriever.vector_store
        store.collection = retriever.collection
        # Upsert-style: delete if exists then add
        try:
            store.collection.delete(ids=[flat_doc["id"]])
        except Exception:
            pass
        store.add_documents([flat_doc], emb)
        return True
    except Exception:
        return False


def run_web_fallback(
    *,
    question: str,
    llm,
    retriever=None,
    grow_kb: bool = False,
    max_results: int = 8,
) -> dict[str, Any]:
    """Search → CoT note → optional KB growth. Free DDG + project LLM."""

    hits = search_duckduckgo(question, max_results=max_results)
    note = synthesize_web_note(question, hits, llm)
    packed = web_note_to_document(note)

    ingested = False
    should = bool(note.get("should_ingest"))
    quality = str(note.get("quality") or "low").lower()
    has_allowlisted = any(h.get("allowlisted") == "1" for h in hits)

    if grow_kb and should and quality in {"high", "medium"} and has_allowlisted:
        if retriever is not None:
            ingested = ingest_web_document(packed["flat"], retriever)

    return {
        "note": note,
        "answer_document": packed["answer_doc"],
        "hits": hits,
        "ingested": ingested,
        "provider": "duckduckgo+llm",
    }
