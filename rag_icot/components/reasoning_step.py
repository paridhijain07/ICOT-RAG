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
        covered_facets=None
    ):

        covered_facets = covered_facets or []
        facet_list = ", ".join(EVIDENCE_FACETS)

        prompt = f"""
You are an expert IoT Cybersecurity reasoning agent.

Your task is NOT to answer the user.
Analyze whether the evidence is sufficient across cybersecurity evidence facets.

Evidence facets (use ONLY these names):
{facet_list}

Question:
{question}

Already covered facets (from retrieved sources):
{covered_facets}

Current Evidence:
{context}

Return ONLY valid JSON:

{{
    "thought": "...",
    "confidence": 0.0,
    "enough_information": false,
    "reason": "...",
    "covered_facets": ["behaviour"],
    "missing_facets": ["vulnerability", "mitigation"],
    "missing_information": ["..."],
    "threat_risk_analysis": "...",
    "next_source": "VARIoT",
    "next_search_query": "..."
}}

Rules:
1. confidence must be between 0 and 1.
2. enough_information=true only if the question can be answered with evidence-backed claims for all facets that the question actually needs.
3. If enough_information=true: next_search_query="" and next_source="".
4. If enough_information=false: choose ONE next_source from [MITRE, VARIoT, IoT23] matching the most important missing facet, and ONE focused next_search_query.
5. Facet mapping guide:
   - behaviour -> IoT23
   - technique / mitigation -> MITRE
   - vulnerability / exploit -> VARIoT
6. Do not invent evidence that is not in Current Evidence.
7. Return ONLY JSON.
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

        if data.get("enough_information"):
            data["next_search_query"] = ""
            data["next_source"] = ""

        return data
