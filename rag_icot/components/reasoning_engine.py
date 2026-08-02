from rag_icot.components.retriever import Retriever
from rag_icot.components.context_manager import ContextManager
from rag_icot.components.reasoning_step import ReasoningStep
from rag_icot.components.context_format import format_documents_for_llm
from rag_icot.constants.evidence_facets import FACET_FILTERS


class ReasoningEngine:

    def __init__(self):

        self.retriever = Retriever()

        self.context_manager = ContextManager()

        self.reasoning_step = ReasoningStep()

    def _build_context(self):
        # Keep prompts under Groq free-tier TPM (~6k tokens/request)
        return format_documents_for_llm(
            self.context_manager.get_documents(),
            max_docs=6,
            max_chars=500,
        )

    def _resolve_filters(self, reasoning):
        """Map next_source / missing_facets to retriever filters."""

        source = reasoning.get("next_source") or None
        missing = reasoning.get("missing_facets") or []

        source_to_preferred_facet = {
            "IoT23": "behaviour",
            "MITRE": "technique",
            "VARIoT": "vulnerability",
        }

        facet = None
        document_type = None

        if source in source_to_preferred_facet:
            preferred = source_to_preferred_facet[source]
            # Prefer a missing facet that matches the chosen source
            for candidate in missing:
                filters = FACET_FILTERS.get(candidate, {})
                if filters.get("source") == source:
                    facet = candidate
                    break
            if facet is None:
                facet = preferred
        elif missing:
            facet = missing[0]

        if facet in FACET_FILTERS:
            filters = FACET_FILTERS[facet]
            source = filters.get("source", source)
            document_type = filters.get("document_type")

        if source not in (None, "MITRE", "VARIoT", "IoT23"):
            source = None
            facet = None
            document_type = None

        return source, document_type, facet

    def reason(
        self,
        question,
        max_iterations=3,
        k=5
    ):

        self.context_manager.clear()

        trace = []

        # Initial broad retrieval
        results = self.retriever.retrieve(
            question,
            k=k
        )

        self.context_manager.add_documents(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0]
        )

        for iteration in range(max_iterations):

            print("\n" + "=" * 80)
            print(f"Iteration {iteration + 1}")
            print("=" * 80)

            covered = self.context_manager.covered_facets()
            context = self._build_context()

            reasoning = self.reasoning_step.run(
                question,
                context,
                covered_facets=covered
            )

            print("Thought:", reasoning.get("thought"))
            print("Confidence:", reasoning.get("confidence"))
            print("Enough Information:", reasoning.get("enough_information"))
            print("Covered Facets:", reasoning.get("covered_facets"))
            print("Missing Facets:", reasoning.get("missing_facets"))
            print("Next Source:", reasoning.get("next_source"))
            print("Reason:", reasoning.get("reason"))
            print(
                "Missing Information:",
                reasoning.get("missing_information")
            )

            trace.append({
                "iteration": iteration + 1,
                "thought": reasoning.get("thought"),
                "confidence": reasoning.get("confidence"),
                "enough_information": reasoning.get("enough_information"),
                "reason": reasoning.get("reason"),
                "covered_facets": reasoning.get("covered_facets"),
                "missing_facets": reasoning.get("missing_facets"),
                "threat_risk_analysis": reasoning.get(
                    "threat_risk_analysis"
                ),
                "missing_information": reasoning.get(
                    "missing_information"
                ),
                "next_source": reasoning.get("next_source"),
                "search_query": reasoning.get("next_search_query"),
                "retrieved_document_ids": list(results["ids"][0]),
                "retrieved_document_count": len(results["ids"][0]),
                "context_facets": covered,
                "context_document_count": len(
                    self.context_manager.get_documents()
                ),
            })

            if reasoning.get("enough_information"):
                print("\nEnough information collected.")
                break

            search_query = reasoning.get("next_search_query") or question

            source, document_type, facet = self._resolve_filters(
                reasoning
            )

            print("\nSearching:", search_query)
            print(
                f"Filters: source={source} "
                f"document_type={document_type} facet={facet}"
            )

            results = self.retriever.retrieve(
                search_query,
                k=k,
                exclude_ids=self.context_manager.get_document_ids(),
                source=source,
                document_type=document_type,
                facet=facet
            )

            self.context_manager.add_documents(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0]
            )

        return {
            "documents": self.context_manager.get_documents(),
            "trace": trace,
            "covered_facets": self.context_manager.covered_facets(),
        }
