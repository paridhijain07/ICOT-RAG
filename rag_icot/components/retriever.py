from rag_icot.components.embedding_builder import EmbeddingBuilder
from rag_icot.components.vector_store import VectorStore


class Retriever:

    def __init__(self):

        self.embedding_builder = EmbeddingBuilder()

        self.vector_store = VectorStore()

        self.collection = self.vector_store.client.get_collection(
            "icot_knowledge"
        )

        self.vector_store.collection = self.collection

    def retrieve(
        self,
        query,
        k=5
    ):

        query_embedding = self.embedding_builder.embed(query)

        results = self.vector_store.search(
            query_embedding,
            k
        )

        return results