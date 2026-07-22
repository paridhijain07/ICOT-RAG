class MITREKnowledgeBuilder:

    def __init__(self):
        pass

    def build(self, documents):

        knowledge = []

        for doc in documents:

            knowledge_doc = {

                "id": doc["id"],

                "source": "MITRE",

                "technique_id": doc["technique_id"],

                "name": doc["name"],

                "description": doc["description"],

                "platforms": doc["platforms"],

                "kill_chain": doc["kill_chain"],

                "detection": doc["detection"],

                "data_sources": doc["data_sources"],

                "metadata": doc["metadata"]

            }

            knowledge.append(knowledge_doc)

        return knowledge