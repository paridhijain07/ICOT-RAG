from rag_icot.components.retriever import Retriever
from rag_icot.components.context_manager import ContextManager
from rag_icot.components.reasoning_step import ReasoningStep


class ReasoningEngine:

    def __init__(self):

        self.retriever = Retriever()

        self.context_manager = ContextManager()

        self.reasoning_step = ReasoningStep()

    def _build_context(self):

        context = ""

        for doc in self.context_manager.get_documents():

            context += doc["text"]

            context += "\n\n"

        return context

    def reason(
        self,
        question,
        max_iterations=3
    ):

        # ---------------------------------------
        # Reset context for a new question
        # ---------------------------------------

        self.context_manager.clear()

        trace = []

        # ---------------------------------------
        # Initial Retrieval
        # ---------------------------------------

        results = self.retriever.retrieve(
            question,
            k=5
        )

        self.context_manager.add_documents(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0]
        )

        # ---------------------------------------
        # ICOT Reasoning Loop
        # ---------------------------------------

        for iteration in range(max_iterations):

            print("\n" + "=" * 80)
            print(f"Iteration {iteration + 1}")
            print("=" * 80)

            context = self._build_context()

            reasoning = self.reasoning_step.run(
                question,
                context
            )

            print("Thought:", reasoning["thought"])
            print("Confidence:", reasoning["confidence"])
            print("Enough Information:", reasoning["enough_information"])
            print("Reason:", reasoning["reason"])
            print("Missing Information:", reasoning["missing_information"])

            # ---------------------------------------
            # Save Reasoning Trace
            # ---------------------------------------

            trace.append({

                "iteration": iteration + 1,

                "thought": reasoning["thought"],

                "confidence": reasoning["confidence"],

                "enough_information": reasoning["enough_information"],

                "reason": reasoning["reason"],

                "missing_information": reasoning["missing_information"],

                "search_query": reasoning["next_search_query"],

                "retrieved_document_ids": results["ids"][0],

                "retrieved_document_count": len(results["ids"][0])

            })

            # ---------------------------------------
            # Stop Condition
            # ---------------------------------------

            if reasoning["enough_information"]:

                print("\n✅ Enough information collected.")

                break

            # ---------------------------------------
            # Retrieve More Evidence
            # ---------------------------------------

            search_query = reasoning["next_search_query"]

            print("\n🔍 Searching:", search_query)

            results = self.retriever.retrieve(
                search_query,
                k=5
            )

            self.context_manager.add_documents(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0]
            )

        # ---------------------------------------
        # Return Final Result
        # ---------------------------------------

        return {

            "documents": self.context_manager.get_documents(),

            "trace": trace

        }