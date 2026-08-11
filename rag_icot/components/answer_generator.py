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

Answer using ONLY the Evidence below. Do not invent CVEs, technique IDs,
malware behaviours, product names, or mitigations that are not supported
by the Evidence.

Rules:
- Prefer concrete facts from the Evidence (scenario names, CVEs, ATT&CK IDs).
- If a section lacks support in the Evidence, write that the evidence is
  insufficient for that point — do not speculate.
- Recommended Mitigations must follow from techniques/vulns present in the
  Evidence (or state that mitigations are not covered).
- References should point to the provided evidence items only.

Generate a professional report with this structure:

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
