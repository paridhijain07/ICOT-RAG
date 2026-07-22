import chromadb


class VectorStore:

    def __init__(
        self,
        persist_directory="../artifacts/chroma_db"
    ):

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = None

    def create_collection(
        self,
        collection_name="icot_knowledge"
    ):

        try:
            self.client.delete_collection(
                collection_name
            )
        except:
            pass

        self.collection = self.client.create_collection(
            name=collection_name
        )

        return self.collection

    def add_documents(
        self,
        documents,
        embeddings
    ):

        ids = []
        texts = []
        metadatas = []
        vectors = []

        for doc, emb in zip(documents, embeddings):

            ids.append(doc["id"])

            text = doc.get(
                "description",
                doc.get("summary", "")
            )

            texts.append(text)

            vectors.append(
                emb.tolist()
            )

            metadata = {}

            for key, value in doc.items():

                if key in ["description", "summary"]:
                    continue

                if isinstance(
                    value,
                    (str, int, float, bool)
                ):
                    metadata[key] = value

                else:
                    metadata[key] = str(value)

            metadatas.append(metadata)

        self.collection.add(

            ids=ids,

            documents=texts,

            embeddings=vectors,

            metadatas=metadatas

        )

    def search(
        self,
        query_embedding,
        k=5
    ):

        return self.collection.query(

            query_embeddings=[
                query_embedding.tolist()
            ],

            n_results=k

        )