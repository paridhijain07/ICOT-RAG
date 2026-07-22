from rag_icot.components.text_cleaner import TextCleaner


class VARIoTKnowledgeBuilder:

    def __init__(self):

        self.cleaner = TextCleaner()

    def build(self, documents):

        knowledge = []

        for i, doc in enumerate(documents):

            knowledge_doc = {

                "id": f"variot_{i}",

                "source": "VARIoT",

                "variot_id": doc["variot_id"],

                "cve": doc["cve"],

                "title": doc["title"],

                "description": self.cleaner.clean(
                    doc["description"]
                ),

                "threat_type": doc["threat_type"]

            }

            knowledge.append(knowledge_doc)

        return knowledge