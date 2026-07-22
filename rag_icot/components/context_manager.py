class ContextManager:

    def __init__(self):

        self.documents = []

        self.document_ids = set()

    def add_documents(
        self,
        ids,
        documents,
        metadatas
    ):

        for doc_id, doc, metadata in zip(
            ids,
            documents,
            metadatas
        ):

            if doc_id in self.document_ids:
                continue

            self.document_ids.add(doc_id)

            self.documents.append({

                "id": doc_id,

                "text": doc,

                "metadata": metadata

            })

    def get_documents(self):

        return self.documents

    def clear(self):

        self.documents = []

        self.document_ids = set()