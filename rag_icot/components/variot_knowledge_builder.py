from rag_icot.components.document_text import enrich_variot_products
from rag_icot.components.text_cleaner import TextCleaner


class VARIoTKnowledgeBuilder:

    def __init__(self):

        self.cleaner = TextCleaner()

    def _normalize_doc(self, doc):

        title = self.cleaner.clean(
            doc.get("title"),
            max_length=300
        )

        # Body only — front-loading happens in build_document_text at index time
        body = self.cleaner.clean(
            doc.get("description"),
            max_length=3000
        )

        products = doc.get("affected_products", [])

        if not isinstance(products, list):
            products = [self.cleaner.extract_field(products)]
        else:
            products = [
                self.cleaner.extract_field(item)
                for item in products
            ]
            products = [p for p in products if p]

        draft = {
            "variot_id": doc.get("variot_id") or doc.get("id"),
            "cve": doc.get("cve") or "",
            "title": title,
            "description": body,
            "threat_type": self.cleaner.extract_field(
                doc.get("threat_type")
            ),
            "affected_products": products,
            "document_type": doc.get(
                "document_type",
                "vulnerability"
            ),
        }

        if not draft["affected_products"]:
            draft["affected_products"] = enrich_variot_products(draft)

        return draft

    def build(self, documents):

        knowledge = []

        for i, doc in enumerate(documents):

            normalized = self._normalize_doc(doc)

            if not normalized["description"]:
                continue

            knowledge_doc = {
                "id": f"variot_vuln_{i}",
                "source": "VARIoT",
                **normalized
            }

            knowledge.append(knowledge_doc)

        return knowledge
