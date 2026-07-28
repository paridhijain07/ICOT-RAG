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

                "metadata": metadata or {}

            })

    def get_documents(self):

        return self.documents

    def get_document_ids(self):

        return set(self.document_ids)

    def covered_facets(self):
        """Infer evidence facets from accumulated document metadata."""

        facets = set()

        for doc in self.documents:

            meta = doc.get("metadata") or {}
            source = meta.get("source")
            doc_type = meta.get("document_type")

            if source == "IoT23":
                facets.add("behaviour")

            elif source == "MITRE":
                facets.add("technique")
                facets.add("mitigation")

            elif source == "VARIoT":
                if doc_type == "exploit":
                    facets.add("exploit")
                else:
                    # vulnerabilities and older docs without type
                    facets.add("vulnerability")
                    if doc_type == "vulnerability":
                        facets.add("vulnerability")

        return sorted(facets)

    def clear(self):

        self.documents = []

        self.document_ids = set()
