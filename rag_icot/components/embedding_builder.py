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

    def embed_documents(self, documents):

        embeddings = []

        for doc in documents:

            text = doc.get(
                "description",
                doc.get("summary", "")
            )

            embeddings.append(
                self.embed(text)
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