"""Answer-quality confidence scorecard (RAG-eval style, no extra LLM calls).

Industry-aligned dimensions (inspired by common RAG eval practice such as
RAGAS-style groundedness / relevance — implemented locally for speed):

- groundedness: claims supported by retrieved context (ID + abstention-aware)
- answer_relevance: question ↔ answer semantic/lexical fit
- context_relevance: question ↔ answer-context fit
- retrieval_support: how tight the dense matches are
- abstention_quality: honest gap admission when context is weak
- overall answer_confidence: weighted usefulness for the user question

Coverage confidence (facet stop) stays separate in the pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Callable

import numpy as np

_INSUFFICIENT = (
    "insufficient",
    "not mentioned",
    "not explicitly",
    "no evidence",
    "not covered",
    "not in the provided",
    "cannot verify",
    "cannot be extracted",
    "do not pertain",
    "unrelated",
    "no data relevant",
    "no information about",
    "was not found",
    "not found in",
    "no cybersecurity threats",
    "consult the official",
)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{2,}", re.I)
_CVE_RE = re.compile(r"cve-\d{4}-\d+", re.I)
_TECH_RE = re.compile(r"\bt\d{4}(?:\.\d{3})?\b", re.I)
_GROUP_RE = re.compile(r"\bg\d{4}\b", re.I)
_SOFT_RE = re.compile(r"\bs\d{4}\b", re.I)

# Transparent weights (sum ≈ 1). Tuned for demo clarity, not paper freeze.
_WEIGHTS = {
    "groundedness": 0.30,
    "answer_relevance": 0.25,
    "context_relevance": 0.20,
    "retrieval_support": 0.15,
    "abstention_quality": 0.10,
}

EmbedFn = Callable[[str], Any]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def _tokens(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "what", "how",
        "are", "was", "were", "does", "did", "about", "into", "your", "have",
        "has", "not", "any", "can", "document", "evidence", "section",
        "summary", "analysis", "threat", "related", "recommended",
    }
    return {
        t.lower()
        for t in _TOKEN_RE.findall(text or "")
        if t.lower() not in stop and len(t) > 2
    }


def _doc_blob(documents: list[dict[str, Any]], max_chars: int = 12000) -> str:
    parts: list[str] = []
    for d in documents or []:
        meta = d.get("metadata") or {}
        parts.append(str(d.get("text") or ""))
        parts.append(str(meta.get("title") or meta.get("name") or ""))
        parts.append(str(meta.get("source") or ""))
        parts.append(str(meta.get("cve") or ""))
        parts.append(str(meta.get("technique_id") or ""))
    blob = "\n".join(parts)
    return blob[:max_chars]


def _lexical_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta))


def _cosine(u: np.ndarray, v: np.ndarray) -> float:
    u = np.asarray(u, dtype=np.float32).reshape(-1)
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    denom = float(np.linalg.norm(u) * np.linalg.norm(v))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(u, v) / denom)


def _semantic_sim(a: str, b: str, embed_fn: EmbedFn | None) -> float | None:
    if embed_fn is None or not (a or "").strip() or not (b or "").strip():
        return None
    try:
        # Truncate for speed — embedding model already loaded in pipeline.
        ea = embed_fn((a or "")[:1500])
        eb = embed_fn((b or "")[:1500])
        # Map cosine [-1,1] → [0,1]
        return _clamp((_cosine(ea, eb) + 1.0) / 2.0)
    except Exception:
        return None


def _blend(lex: float, sem: float | None, sem_weight: float = 0.65) -> float:
    if sem is None:
        return _clamp(lex)
    return _clamp((1.0 - sem_weight) * lex + sem_weight * sem)


def _extract_ids(text: str) -> list[str]:
    t = text or ""
    ids = (
        [m.lower() for m in _CVE_RE.findall(t)]
        + [m.lower() for m in _TECH_RE.findall(t)]
        + [m.lower() for m in _GROUP_RE.findall(t)]
        + [m.lower() for m in _SOFT_RE.findall(t)]
    )
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _admits_insufficient(answer: str) -> bool:
    a = (answer or "").lower()
    return any(p in a for p in _INSUFFICIENT)


def _groundedness(answer: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Citation / ID support + honesty when no IDs."""

    blob = _doc_blob(documents).lower()
    ids = _extract_ids(answer)
    supported = [i for i in ids if i in blob]
    unsupported = [i for i in ids if i not in blob]
    admits = _admits_insufficient(answer)

    if ids:
        rate = len(supported) / len(ids)
        note = f"ids {len(supported)}/{len(ids)} grounded"
    else:
        # No IDs: honest abstention scores high on groundedness;
        # confident invention without IDs scores mid-low.
        rate = 0.92 if admits else 0.45
        note = "abstention_grounded" if admits else "no_ids_neutral"

    return {
        "score": _clamp(rate),
        "supported_ids": supported,
        "unsupported_ids": unsupported,
        "note": note,
    }


def _retrieval_support(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Map dense distances to [0,1] (lower distance → higher support)."""

    dists = [
        float(d["distance"])
        for d in (documents or [])
        if d.get("distance") is not None
        and str((d.get("metadata") or {}).get("source") or "").upper() != "WEB"
    ]
    if not dists:
        # Web-only or missing distances
        has_web = any(
            str((d.get("metadata") or {}).get("source") or "").upper() == "WEB"
            for d in (documents or [])
        )
        return {
            "score": 0.40 if has_web else 0.30,
            "avg_distance": None,
            "note": "web_only_or_no_distance" if has_web else "no_distances",
        }

    avg = sum(dists) / len(dists)
    # Soft map: dist 0.3 → ~0.9, dist 1.2 → ~0.25 (typical unit-embed L2/cos range)
    score = _clamp(1.15 - 0.75 * avg)
    return {
        "score": score,
        "avg_distance": round(avg, 3),
        "note": f"avg_distance={avg:.3f}",
    }


def _abstention_quality(
    *,
    admits: bool,
    context_relevance: float,
    groundedness: float,
) -> dict[str, Any]:
    """Good systems abstain when context is weak; bad systems abstain when strong."""

    if admits:
        # Reward refusing weak context; penalize refusing strong context.
        if context_relevance < 0.35:
            score = 0.85 + 0.1 * groundedness
            note = "correct_abstention_weak_context"
        elif context_relevance > 0.55:
            score = 0.25
            note = "over_abstention_strong_context"
        else:
            score = 0.55
            note = "borderline_abstention"
    else:
        if context_relevance < 0.25:
            score = 0.20
            note = "answered_despite_weak_context"
        else:
            score = 0.70
            note = "answered_with_usable_context"
    return {"score": _clamp(score), "note": note}


def coverage_confidence_from_trace(trace: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not trace:
        return {"coverage_confidence": None, "coverage_reason": "no_trace"}
    last = trace[-1] or {}
    conf = last.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf_f = None
    return {
        "coverage_confidence": conf_f,
        "coverage_reason": last.get("stop_reason")
        or last.get("reason")
        or "trace_last_step",
    }


def score_answer_confidence(
    *,
    question: str,
    answer: str,
    documents: list[dict[str, Any]] | None,
    web_fallback: dict[str, Any] | None = None,
    embed_fn: EmbedFn | None = None,
) -> dict[str, Any]:
    """RAG-style multi-dimension confidence; overall = user-usefulness score."""

    docs = documents or []
    web = web_fallback or {}
    ctx = _doc_blob(docs)
    admits = _admits_insufficient(answer)

    g = _groundedness(answer, docs)

    ans_lex = _lexical_overlap(question, answer)
    ans_sem = _semantic_sim(question, answer, embed_fn)
    answer_relevance = _blend(ans_lex, ans_sem)

    ctx_lex = _lexical_overlap(question, ctx)
    ctx_sem = _semantic_sim(question, ctx[:2000], embed_fn)
    context_relevance = _blend(ctx_lex, ctx_sem)

    # Web note can lift context relevance slightly when used & decent quality
    if web.get("used"):
        wq = str(web.get("quality") or "low").lower()
        bump = {"high": 0.12, "medium": 0.06, "low": 0.0}.get(wq, 0.0)
        if any(str(s.get("allowlisted")) == "1" for s in (web.get("sources") or [])):
            bump += 0.04
        context_relevance = _clamp(context_relevance + bump)

    r = _retrieval_support(docs)
    a = _abstention_quality(
        admits=admits,
        context_relevance=context_relevance,
        groundedness=g["score"],
    )

    dims = {
        "groundedness": round(g["score"], 3),
        "answer_relevance": round(answer_relevance, 3),
        "context_relevance": round(context_relevance, 3),
        "retrieval_support": round(r["score"], 3),
        "abstention_quality": round(a["score"], 3),
    }

    # User-facing usefulness (“did we answer the question?”).
    # Correct abstention ⇒ high abstention_quality, but LOW overall confidence.
    if admits:
        usefulness = (
            0.20 * dims["groundedness"]
            + 0.15 * dims["answer_relevance"]
            + 0.25 * dims["context_relevance"]
            + 0.15 * dims["retrieval_support"]
            + 0.25 * dims["abstention_quality"]
        )
        # Hard cap: refusing to answer cannot look like a high-quality answer.
        usefulness = min(usefulness, 0.38)
        mode = "abstained"
    else:
        usefulness = sum(dims[k] * _WEIGHTS[k] for k in _WEIGHTS)
        mode = "standard"

    # Short answer penalty
    if len((answer or "").strip()) < 80:
        usefulness *= 0.85

    usefulness = _clamp(usefulness)
    label = (
        "high" if usefulness >= 0.70 else "medium" if usefulness >= 0.45 else "low"
    )

    reasons = [
        f"mode={mode}",
        f"groundedness={dims['groundedness']} ({g['note']})",
        f"answer_relevance={dims['answer_relevance']}",
        f"context_relevance={dims['context_relevance']}",
        f"retrieval_support={dims['retrieval_support']} ({r['note']})",
        f"abstention_quality={dims['abstention_quality']} ({a['note']})",
    ]
    if ans_sem is not None:
        reasons.append(f"semantic_qa={ans_sem:.2f}")
    if ctx_sem is not None:
        reasons.append(f"semantic_qc={ctx_sem:.2f}")
    if g["unsupported_ids"]:
        reasons.append("unsupported:" + ",".join(g["unsupported_ids"][:4]))

    return {
        "answer_confidence": round(usefulness, 3),
        "answer_confidence_label": label,
        "answer_confidence_reason": "; ".join(reasons),
        "answer_confidence_dimensions": dims,
        "answer_confidence_weights": dict(_WEIGHTS),
        "faithfulness_rate": dims["groundedness"],
        "question_doc_overlap": round(ctx_lex, 3),
        "avg_retrieval_distance": r.get("avg_distance"),
        "admits_insufficient": admits,
    }
