"""LLM-as-judge scoring for RAG answers.

Scores are 1–5 on ChatIoT-style dimensions plus an overall mean.
The judge must prefer evidence-grounded answers and reward honest
insufficiency when the KB cannot support the question.
"""

from __future__ import annotations

import json
from typing import Any

from rag_icot.components.llm import GeminiLLM

JUDGE_DIMENSIONS = (
    "reliability",
    "relevance",
    "technicality",
    "friendliness",
)


def _parse_json(response: str) -> dict[str, Any]:
    text = (response or "").strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    if text.startswith("```"):
        text = text.replace("```", "", 1)
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def _clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 1.0
    return max(1.0, min(5.0, score))


class AnswerJudge:
    """Score an answer with an LLM judge (same provider as generation)."""

    def __init__(self, llm: GeminiLLM | None = None):
        self.llm = llm or GeminiLLM()

    def score(
        self,
        question: str,
        answer: str,
        gold_notes: str = "",
        reference_hints: list[str] | None = None,
        evidence_preview: str = "",
    ) -> dict[str, Any]:
        hints = ", ".join(reference_hints or []) or "(none)"
        notes = gold_notes or "(none)"
        evidence = (evidence_preview or "(not provided)")[:2500]
        answer_text = (answer or "")[:3500]

        prompt = f"""
You are an expert IoT cybersecurity evaluation judge.

Score the ANSWER to the QUESTION on a 1–5 integer scale for each dimension.
Use ONLY the question, optional gold notes/hints, and evidence preview.
Do not reward fluent hallucination.

Dimensions:
- reliability: grounded in evidence; no invented facts; admits insufficiency when needed
- relevance: directly addresses the question
- technicality: correct technical depth for IoT security / ATT&CK / CVEs / malware behaviour
- friendliness: clear, structured, usable for an analyst (not vague filler)

QUESTION:
{question}

GOLD NOTES:
{notes}

REFERENCE HINTS:
{hints}

EVIDENCE PREVIEW (may be truncated):
{evidence}

ANSWER:
{answer_text}

Return ONLY valid JSON:
{{
  "reliability": 1,
  "relevance": 1,
  "technicality": 1,
  "friendliness": 1,
  "justification": "one short paragraph"
}}
"""
        raw = self.llm.generate(prompt)
        data = _parse_json(raw)

        scores = {
            dim: _clamp_score(data.get(dim))
            for dim in JUDGE_DIMENSIONS
        }
        scores["overall"] = sum(scores.values()) / len(JUDGE_DIMENSIONS)
        scores["justification"] = str(data.get("justification") or "").strip()
        return scores


def summarize_judge_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Average judge scores per baseline key (e.g. vanilla / facet_icot)."""

    from collections import defaultdict

    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:
        for baseline, payload in row.get("judges", {}).items():
            for dim in (*JUDGE_DIMENSIONS, "overall"):
                if dim in payload:
                    buckets[baseline][dim].append(float(payload[dim]))

    summary: dict[str, Any] = {}
    for baseline, dims in buckets.items():
        summary[baseline] = {
            dim: (sum(vals) / len(vals) if vals else 0.0)
            for dim, vals in dims.items()
        }
        summary[baseline]["n"] = len(next(iter(dims.values()), []))
    return summary
