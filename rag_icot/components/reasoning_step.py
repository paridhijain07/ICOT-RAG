import json

from rag_icot.components.llm import GeminiLLM
from rag_icot.constants.evidence_facets import EVIDENCE_FACETS


class ReasoningStep:

    def __init__(self):

        self.llm = GeminiLLM()

    def _parse_json(self, response):

        response = response.strip()

        if response.startswith("```json"):
            response = response.replace("```json", "", 1)

        if response.startswith("```"):
            response = response.replace("```", "", 1)

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(response[start:end + 1])

    def run(
        self,
        question,
        context,
        covered_facets=None,
        needed_facets=None,
    ):
        """Decide sufficiency for the facets this question needs.

        ``needed_facets`` scopes missing/enough checks so the reasoner does
        not demand every evidence type for every question.
        """

        covered_facets = covered_facets or []
        needed_facets = [
            f for f in (needed_facets or list(EVIDENCE_FACETS))
            if f in EVIDENCE_FACETS
        ] or list(EVIDENCE_FACETS)

        facet_list = ", ".join(EVIDENCE_FACETS)
        needed_list = ", ".join(needed_facets)
        still_missing = [
            f for f in needed_facets if f not in set(covered_facets)
        ]

        prompt = f"""
You are an expert IoT Cybersecurity reasoning agent.

Your task is NOT to answer the user.
Decide whether retrieved evidence is sufficient for the facets this
question actually needs, and if not, propose ONE focused retrieval.

All evidence facet names (use ONLY these):
{facet_list}

Facets this question NEEDS (ignore facets not in this list):
{needed_list}

Question:
{question}

Already covered facets (from retrieved sources):
{covered_facets}

Still missing among needed facets:
{still_missing}

Current Evidence:
{context}

Return ONLY valid JSON:

{{
    "thought": "Brief analysis of whether needed facets are covered.",
    "confidence": 0.7,
    "enough_information": false,
    "reason": "...",
    "covered_facets": ["behaviour"],
    "missing_facets": ["technique"],
    "missing_information": ["..."],
    "threat_risk_analysis": "...",
    "next_source": "MITRE",
    "next_search_query": "..."
}}

Rules:
1. confidence must be between 0 and 1 (use higher confidence when needed facets are clearly covered).
2. missing_facets MUST be a subset of the needed facets list only: [{needed_list}].
3. enough_information=true ONLY if every needed facet is supported by Current Evidence (or clearly not required because evidence already answers the question for those facets).
4. Do NOT require vulnerability/exploit/mitigation/behaviour/technique unless it appears in the needed facets list.
5. If enough_information=true: next_search_query="" and next_source="" and missing_facets=[].
6. If enough_information=false: choose ONE next_source from [MITRE, VARIoT, IoT23] matching the most important missing needed facet, and ONE focused next_search_query.
7. Facet mapping guide:
   - behaviour -> IoT23
   - technique / mitigation -> MITRE
   - vulnerability / exploit -> VARIoT
8. Do not invent evidence that is not in Current Evidence.
9. Return ONLY JSON.
"""

        response = self.llm.generate(prompt)
        data = self._parse_json(response)

        # Normalize optional fields for older callers
        data.setdefault("covered_facets", covered_facets)
        data.setdefault("missing_facets", [])
        data.setdefault("threat_risk_analysis", "")
        data.setdefault("next_source", "")
        data.setdefault("missing_information", [])
        data.setdefault("next_search_query", "")

        # Keep missing list scoped to needed facets
        needed_set = set(needed_facets)
        raw_missing = data.get("missing_facets") or []
        if not isinstance(raw_missing, list):
            raw_missing = []
        data["missing_facets"] = [
            f for f in raw_missing if f in needed_set
        ]
        # If model omitted missings, fall back to deterministic gap
        if not data.get("enough_information") and not data["missing_facets"]:
            data["missing_facets"] = list(still_missing)

        if data.get("enough_information"):
            data["next_search_query"] = ""
            data["next_source"] = ""
            data["missing_facets"] = []

        return data
