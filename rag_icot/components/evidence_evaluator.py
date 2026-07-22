import json

from rag_icot.components.llm import GeminiLLM


class EvidenceEvaluator:

    def __init__(self):

        self.llm = GeminiLLM()

    def evaluate(
        self,
        question,
        context
    ):

        prompt = f"""
You are an expert IoT Cybersecurity reasoning evaluator.

Question:
{question}

Current Evidence:
{context}

Evaluate whether the available evidence is sufficient to answer the question.

Return ONLY valid JSON.

Example:

{{
    "enough_information": false,
    "reason": "Current evidence explains Mirai attacks but lacks mitigation details.",
    "missing_information": [
        "Mitigation strategies",
        "Related vulnerabilities"
    ]
}}

Rules:

- Return ONLY JSON.
- Do not explain outside JSON.
- Do not use markdown.
"""

        response = self.llm.generate(prompt)

        response = response.strip()

        if response.startswith("```json"):
            response = response.replace("```json", "")

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        return json.loads(response)