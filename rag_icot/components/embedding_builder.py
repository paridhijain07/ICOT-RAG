from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingBuilder:

    def __init__(
        self,
        model_name="BAAI/bge-small-en-v1.5"
    ):

        self.model = SentenceTransformer(
            model_name
        )

    def embed(self, text):

        return self.model.encode(
            text,
            normalize_embeddings=True
        )

    def get_embed_text(self, doc):
        from rag_icot.components.document_text import build_document_text

        return build_document_text(doc)

    def embed_documents(self, documents, batch_size=64):

        texts = [
            self.get_embed_text(doc)
            for doc in documents
        ]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return np.array(embeddings)

    def save_embeddings(
        self,
        embeddings,
        file_path
    ):

        np.save(
            file_path,
            embeddings
        )

        print(
            f"Saved embeddings to {file_path}"
        )

    def load_embeddings(
        self,
        file_path
    ):

        return np.load(
            file_path
        )