"""Truncate retrieved evidence so Groq free-tier TPM limits are not blown."""

from __future__ import annotations

from typing import Any


DEFAULT_MAX_DOCS = 8
DEFAULT_MAX_CHARS = 700


def truncate_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def format_documents_for_llm(
    documents: list[dict[str, Any]],
    max_docs: int = DEFAULT_MAX_DOCS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Build a bounded evidence block for prompts."""

    parts: list[str] = []
    for i, doc in enumerate(documents[:max_docs], start=1):
        meta = doc.get("metadata") or {}
        source = meta.get("source") or doc.get("source") or "unknown"
        title = (
            meta.get("title")
            or meta.get("name")
            or doc.get("title")
            or doc.get("name")
            or doc.get("id")
            or f"doc_{i}"
        )
        text = truncate_text(doc.get("text") or "", max_chars=max_chars)
        parts.append(
            f"==============================\n"
            f"Document {i} [{source}] {title}\n"
            f"==============================\n\n"
            f"{text}\n"
        )

    omitted = max(0, len(documents) - max_docs)
    if omitted:
        parts.append(f"\n[{omitted} additional retrieved docs omitted for length]\n")

    return "\n".join(parts)
