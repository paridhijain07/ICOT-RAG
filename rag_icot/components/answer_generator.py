from rag_icot.components.llm import GeminiLLM
from rag_icot.components.context_format import format_documents_for_llm


class AnswerGenerator:

    def __init__(self):

        self.llm = GeminiLLM()

    def generate(
        self,
        question,
        documents
    ):

        context = format_documents_for_llm(documents)

        prompt = f"""
You are an expert IoT Cybersecurity Analyst.

Use ONLY the provided evidence to answer the question.

If the evidence is insufficient, clearly mention it.

Generate a professional report using the following structure:

1. Executive Summary

2. Threat Analysis

3. Evidence Found

4. MITRE ATT&CK Mapping

5. Related Vulnerabilities

6. Recommended Mitigations

7. References

Question:

{question}

Evidence:

{context}
"""

        return self.llm.generate(prompt)
