"""Zeng-style prompt-only Iterative Chain-of-Thought (no retrieval).

Inspired by prompt-only ICoT for IoT security analysis: expert role,
multi-step reasoning, then advice — without a knowledge base.
"""

from __future__ import annotations

from rag_icot.components.llm import GeminiLLM


class PromptOnlyICOT:
    """Prompt-only ICoT baseline (no RAG / no vector store)."""

    def __init__(self, llm: GeminiLLM | None = None):
        self.llm = llm or GeminiLLM()

    def run(self, question: str) -> dict:
        """Run 3 reasoning stages, then produce a final report."""

        analysis = self._stage_analyze(question)
        expansion = self._stage_expand(question, analysis)
        answer = self._stage_answer(question, analysis, expansion)

        trace = [
            {
                "iteration": 1,
                "stage": "role_threat_analysis",
                "thought": analysis,
                "confidence": None,
                "enough_information": False,
                "reason": "Prompt-only stage 1: expert role + threat decomposition",
                "next_source": "",
                "search_query": "",
            },
            {
                "iteration": 2,
                "stage": "technical_expansion",
                "thought": expansion,
                "confidence": None,
                "enough_information": False,
                "reason": "Prompt-only stage 2: techniques / vulns / mitigations reasoning",
                "next_source": "",
                "search_query": "",
            },
            {
                "iteration": 3,
                "stage": "final_advice",
                "thought": "Generated final structured IoT security report from prior CoT stages.",
                "confidence": None,
                "enough_information": True,
                "reason": "Prompt-only stage 3: final answer (no retrieval)",
                "next_source": "",
                "search_query": "",
            },
        ]

        return {
            "answer": answer,
            "trace": trace,
            "analysis": analysis,
            "expansion": expansion,
        }

    def _stage_analyze(self, question: str) -> str:
        prompt = f"""
You are a senior IoT cybersecurity expert (role-based ICoT stage 1).

Do NOT use external documents. Reason only from your knowledge.

Question:
{question}

Produce a short chain-of-thought analysis covering:
1. What the question is asking
2. Likely threat actors / malware / vulnerability class (if applicable)
3. Which evidence types would ideally be needed (behaviour, technique,
   vulnerability, exploit, mitigation) — note you have NO retrieved evidence
4. Key uncertainties / what you cannot verify without a knowledge base

Write clearly in plain prose (no JSON). Keep under 350 words.
"""
        return self.llm.generate(prompt)

    def _stage_expand(self, question: str, analysis: str) -> str:
        prompt = f"""
You are a senior IoT cybersecurity expert (role-based ICoT stage 2).

Continue iterative chain-of-thought. Still NO external documents.

Question:
{question}

Stage-1 analysis:
{analysis}

Expand the reasoning with:
1. Plausible network behaviours / attack steps
2. Related MITRE ATT&CK techniques (best effort; mark guesses)
3. Related vulnerabilities / CVEs only if you are reasonably sure;
   otherwise say unknown
4. Practical mitigations

Be explicit when inventing vs recalling. Keep under 400 words.
"""
        return self.llm.generate(prompt)

    def _stage_answer(
        self,
        question: str,
        analysis: str,
        expansion: str,
    ) -> str:
        prompt = f"""
You are a senior IoT cybersecurity expert (role-based ICoT stage 3 — final advice).

Use the prior reasoning stages. Do NOT claim you retrieved a knowledge base.
If something is uncertain, say so.

Question:
{question}

Stage-1 analysis:
{analysis}

Stage-2 expansion:
{expansion}

Generate a professional report using this structure:

1. Executive Summary
2. Threat Analysis
3. Evidence Found (state clearly: no retrieved KB evidence; reasoning-only)
4. MITRE ATT&CK Mapping
5. Related Vulnerabilities
6. Recommended Mitigations
7. References (label as model knowledge / general references only)
"""
        return self.llm.generate(prompt)
