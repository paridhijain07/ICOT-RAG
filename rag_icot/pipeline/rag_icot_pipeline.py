from rag_icot.components.reasoning_engine import ReasoningEngine
from rag_icot.components.answer_generator import AnswerGenerator
from rag_icot.components.answer_context import select_answer_documents
from rag_icot.components.web_research import kb_evidence_weak, run_web_fallback
from rag_icot.components.answer_confidence import (
    coverage_confidence_from_trace,
    score_answer_confidence,
)


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
        web_fallback=False,
        grow_kb=False,
    ):
        """Run iterative ICOT-RAG and return answer + explainable trace.

        By default the final answer is generated from a facet-balanced
        subset of retrieved docs (not the full accumulated pile).

        Optional demo-only web fallback (free DuckDuckGo + project LLM):
        if local KB evidence looks weak, research the web and optionally
        ingest a quality note into Chroma. Keep web_fallback=False for
        frozen paper evaluation.

        Returns both:
        - coverage_confidence: ICOT facet/stop confidence (trace)
        - answer_confidence: heuristic answer-quality score
        """

        result = self.engine.reason(
            question,
            max_iterations=max_iterations,
            required_facets=required_facets,
            multisource_init=True,
        )

        all_docs = result["documents"]
        covered = result.get("covered_facets", [])
        needed = result.get("needed_facets") or required_facets
        trace = result.get("trace") or []

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

        web_meta = {
            "used": False,
            "triggered": False,
            "reason": "disabled",
            "ingested": False,
        }

        if web_fallback:
            weak, reason = kb_evidence_weak(
                answer=answer,
                documents=answer_docs or all_docs,
                needed_facets=needed,
                covered_facets=covered,
            )
            web_meta["reason"] = reason
            web_meta["triggered"] = weak
            if weak:
                try:
                    llm = self.generator.llm
                    retriever = self.engine.retriever
                    web = run_web_fallback(
                        question=question,
                        llm=llm,
                        retriever=retriever,
                        grow_kb=grow_kb,
                    )
                    web_doc = web["answer_document"]
                    answer_docs = list(answer_docs or []) + [web_doc]
                    all_docs = list(all_docs or []) + [web_doc]
                    # Regenerate with KB + web note
                    answer = self.generator.generate(question, answer_docs)
                    web_meta.update(
                        {
                            "used": True,
                            "ingested": bool(web.get("ingested")),
                            "quality": (web.get("note") or {}).get("quality"),
                            "should_ingest": (web.get("note") or {}).get(
                                "should_ingest"
                            ),
                            "sources": (web.get("note") or {}).get("sources")
                            or [],
                            "provider": web.get("provider"),
                            "hits": len(web.get("hits") or []),
                        }
                    )
                except Exception as exc:
                    web_meta["error"] = f"{type(exc).__name__}: {exc}"

        coverage = coverage_confidence_from_trace(trace)
        embed_fn = self.engine.retriever.embedding_builder.embed
        quality = score_answer_confidence(
            question=question,
            answer=answer,
            documents=answer_docs,
            web_fallback=web_meta,
            embed_fn=embed_fn,
        )

        return {
            "answer": answer,
            "documents": all_docs,
            "answer_documents": answer_docs,
            "trace": trace,
            "covered_facets": covered,
            "needed_facets": needed,
            "web_fallback": web_meta,
            **coverage,
            **quality,
        }
