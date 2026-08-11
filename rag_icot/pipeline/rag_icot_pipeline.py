from rag_icot.components.reasoning_engine import ReasoningEngine
from rag_icot.components.answer_generator import AnswerGenerator
from rag_icot.components.answer_context import select_answer_documents


class RAGICOTPipeline:

    def __init__(self):

        self.engine = ReasoningEngine()

        self.generator = AnswerGenerator()

    def run(
        self,
        question,
        max_iterations=3,
        required_facets=None,
        filter_answer_context=True,
        max_answer_docs=6,
        max_per_facet=2,
    ):
        """Run iterative ICOT-RAG and return answer + explainable trace.

        By default the final answer is generated from a facet-balanced
        subset of retrieved docs (not the full accumulated pile).
        """

        result = self.engine.reason(
            question,
            max_iterations=max_iterations,
            required_facets=required_facets,
            multisource_init=True,
        )

        all_docs = result["documents"]
        covered = result.get("covered_facets", [])

        if filter_answer_context:
            answer_docs = select_answer_documents(
                all_docs,
                question=question,
                covered_facets=covered,
                required_facets=required_facets,
                max_per_facet=max_per_facet,
                max_total=max_answer_docs,
            )
        else:
            answer_docs = all_docs

        answer = self.generator.generate(
            question,
            answer_docs
        )

        return {
            "answer": answer,
            "documents": all_docs,
            "answer_documents": answer_docs,
            "trace": result["trace"],
            "covered_facets": covered,
            "needed_facets": result.get("needed_facets") or required_facets,
        }
