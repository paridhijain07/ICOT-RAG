class PromptBuilder:

    def __init__(self):
        pass

    def build(
        self,
        query,
        retrieved_documents
    ):

        context = ""

        for i, doc in enumerate(retrieved_documents):

            context += f"""
============================
Document {i+1}
============================

{doc}

"""

        prompt = f"""
You are an expert IoT Cybersecurity Analyst.

Answer ONLY using the information provided below.

If the information is insufficient, clearly state that.

============================
CONTEXT
============================

{context}

============================
QUESTION
============================

{query}

============================
ANSWER
============================
"""

        return prompt