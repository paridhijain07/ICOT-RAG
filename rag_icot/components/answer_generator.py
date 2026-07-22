from rag_icot.components.llm import GeminiLLM


class AnswerGenerator:

    def __init__(self):

        self.llm = GeminiLLM()

    def generate(
        self,
        question,
        documents
    ):

        context = ""

        for i, doc in enumerate(documents):

            context += f"""
==============================
Document {i+1}
==============================

{doc["text"]}

"""

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