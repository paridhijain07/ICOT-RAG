from rag_icot.components.llm import GeminiLLM


class ThoughtGenerator:

    def __init__(self):

        self.llm = GeminiLLM()

    def generate(
        self,
        question,
        context
    ):

        prompt = f"""
You are an expert IoT Cybersecurity reasoning agent.

You are NOT answering the user.

Your job is ONLY to decide what information is still missing.

Current Question:

{question}

Current Knowledge:

{context}

Think carefully.

If you already have enough information,
set retrieve=false.

Otherwise,
set retrieve=true
and generate the next search query.

Return ONLY a JSON object.

Example:

{{
    "thought": "I already know how Mirai performs DDoS attacks but I need related vulnerabilities.",
    "retrieve": true,
    "search_query": "Mirai vulnerabilities CVE"
}}

Do not write explanations.
Do not use markdown.
Do not wrap the JSON in ```json.
Return ONLY the JSON.
"""

        response = self.llm.generate(
            prompt
        )

        return response