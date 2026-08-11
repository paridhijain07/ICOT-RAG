from rag_icot.components.retriever import Retriever
from rag_icot.components.context_manager import ContextManager
from rag_icot.components.reasoning_step import ReasoningStep
from rag_icot.components.context_format import format_documents_for_llm
from rag_icot.components.answer_context import infer_needed_facets
from rag_icot.constants.evidence_facets import FACET_FILTERS, VALID_SOURCES


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

    def _multisource_retrieve(
        self,
        question,
        k_per_source=3,
        max_docs=8,
        exclude_ids=None,
    ):
        """ChatIoT-style per-source retrieve + merge (initial fill)."""

        exclude_ids = set(exclude_ids or [])
        merged = {}

        for source in VALID_SOURCES:
            results = self.retriever.retrieve(
                question,
                k=k_per_source,
                source=source,
                exclude_ids=exclude_ids,
            )
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = (results.get("distances") or [[]])[0]
            for doc_id, text, meta, dist in zip(ids, docs, metas, dists):
                if doc_id in exclude_ids:
                    continue
                prev = merged.get(doc_id)
                dist_f = float(dist) if dist is not None else 1e9
                if prev is None or dist_f < float(prev["distance"]):
                    merged[doc_id] = {
                        "id": doc_id,
                        "text": text,
                        "metadata": meta or {},
                        "distance": dist_f,
                    }

        ranked = sorted(merged.values(), key=lambda d: d["distance"])[:max_docs]
        return {
            "ids": [d["id"] for d in ranked],
            "documents": [d["text"] for d in ranked],
            "metadatas": [d["metadata"] for d in ranked],
        }

    def _needed_missing(self, needed_facets):
        covered = set(self.context_manager.covered_facets())
        return [f for f in needed_facets if f not in covered]

    def reason(
        self,
        question,
        max_iterations=3,
        k=5,
        required_facets=None,
        multisource_init=True,
        k_per_source=3,
        max_init_docs=8,
    ):
        """Facet-aware iterative retrieve–reason–retrieve.

        By default starts with a multi-source retrieve (strong coverage),
        then only re-retrieves for facets the question still needs.
        """

        self.context_manager.clear()

        needed_facets = infer_needed_facets(
            question,
            required_facets=required_facets,
        )
        print(f"Needed facets: {needed_facets}", flush=True)

        trace = []
        last_retrieve_ids = []

        # --- Initial retrieval ---
        if multisource_init:
            print(
                f"Initial multi-source retrieve "
                f"(k_per_source={k_per_source}, max={max_init_docs})",
                flush=True,
            )
            packed = self._multisource_retrieve(
                question,
                k_per_source=k_per_source,
                max_docs=max_init_docs,
            )
            last_retrieve_ids = list(packed["ids"])
            self.context_manager.add_documents(
                packed["ids"],
                packed["documents"],
                packed["metadatas"],
            )
        else:
            results = self.retriever.retrieve(question, k=k)
            last_retrieve_ids = list(results["ids"][0])
            self.context_manager.add_documents(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
            )

        for iteration in range(max_iterations):

            print("\n" + "=" * 80)
            print(f"Iteration {iteration + 1}")
            print("=" * 80)

            covered = self.context_manager.covered_facets()
            missing_needed = self._needed_missing(needed_facets)
            context = self._build_context()

            # Deterministic early stop: all needed facets already present
            if not missing_needed:
                print(
                    "All needed facets covered — skipping further retrieve.",
                    flush=True,
                )
                trace.append({
                    "iteration": iteration + 1,
                    "thought": (
                        "Deterministic stop: all needed facets are covered "
                        f"({needed_facets})."
                    ),
                    "confidence": 0.85,
                    "enough_information": True,
                    "reason": "Needed facets covered after retrieval.",
                    "covered_facets": covered,
                    "missing_facets": [],
                    "threat_risk_analysis": "",
                    "missing_information": [],
                    "next_source": "",
                    "search_query": "",
                    "retrieved_document_ids": list(last_retrieve_ids),
                    "retrieved_document_count": len(last_retrieve_ids),
                    "context_facets": covered,
                    "context_document_count": len(
                        self.context_manager.get_documents()
                    ),
                    "needed_facets": needed_facets,
                    "stop_reason": "needed_facets_covered",
                })
                break

            reasoning = self.reasoning_step.run(
                question,
                context,
                covered_facets=covered,
                needed_facets=needed_facets,
            )

            # Override LLM enough-flag using metadata coverage of needed facets
            missing_needed = self._needed_missing(needed_facets)
            if not missing_needed:
                reasoning["enough_information"] = True
                reasoning["missing_facets"] = []
                reasoning["next_search_query"] = ""
                reasoning["next_source"] = ""
            else:
                # Keep model missings aligned with real gaps
                model_missing = reasoning.get("missing_facets") or []
                aligned = [f for f in model_missing if f in missing_needed]
                reasoning["missing_facets"] = aligned or list(missing_needed)
                if reasoning.get("enough_information"):
                    # Model claimed enough but metadata gaps remain — continue
                    reasoning["enough_information"] = False

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
                "retrieved_document_ids": list(last_retrieve_ids),
                "retrieved_document_count": len(last_retrieve_ids),
                "context_facets": covered,
                "context_document_count": len(
                    self.context_manager.get_documents()
                ),
                "needed_facets": needed_facets,
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
                facet=facet,
            )
            last_retrieve_ids = list(results["ids"][0])

            self.context_manager.add_documents(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
            )

        return {
            "documents": self.context_manager.get_documents(),
            "trace": trace,
            "covered_facets": self.context_manager.covered_facets(),
            "needed_facets": needed_facets,
        }
