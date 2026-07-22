import json

from rag_icot.components.llm import GeminiLLM


class ReasoningStep:

    def __init__(self):

        self.llm = GeminiLLM()

    def run(
        self,
        question,
        context
    ):

        prompt = f"""
You are an expert IoT Cybersecurity reasoning agent.

Your task is NOT to answer the user.

Instead, analyze the current evidence and decide whether more information is needed.

Question:

{question}

Current Evidence:

{context}

Return ONLY valid JSON.

Format:

{{
    "thought": "...",

    "confidence": 0.0,

    "enough_information": false,

    "reason": "...",

    "missing_information": [
        "...",
        "..."
    ],

    "next_search_query": "..."
}}

Rules:

1. confidence must be between 0 and 1.

2. enough_information must be true or false.

3. If enough_information=true,
   next_search_query must be "".

4. If enough_information=false,
   generate ONE focused search query.

5. Return ONLY JSON.
"""

        response = self.llm.generate(
            prompt
        )

        response = response.strip()

        if response.startswith("```json"):
            response = response.replace(
                "```json",
                ""
            )

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        return json.loads(response)