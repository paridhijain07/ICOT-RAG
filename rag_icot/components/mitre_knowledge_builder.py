class MITREKnowledgeBuilder:

    # Platforms most relevant to IoT / network / edge security Q&A
    KEEP_PLATFORMS = {
        "Linux",
        "Network Devices",
        "Containers",
        "IaaS",
        "PRE",
        "Android",
        "iOS",
        "Field Controller/RTU/PLC/IED",
        "Engineering Workstation",
    }

    # Keep Windows/macOS techniques only when text clearly matches these themes
    IOT_KEYWORDS = (
        "botnet",
        "firmware",
        "router",
        "default credential",
        "telnet",
        "brute force",
        "denial of service",
        "command and control",
        "network denial",
        "remote services",
        "valid accounts",
        "exploit public-facing",
        "network sniffing",
        "endpoint denial",
        "resource hijacking",
        "iot",
        "camera",
        "dvr",
        "proxy",
        "lateral tool transfer",
        "ingress tool transfer",
        "application layer protocol",
        "encrypted channel",
        "non-application layer protocol",
        "compromise infrastructure",
        "external remote services",
        "network service discovery",
        "remote system discovery",
        "password spraying",
        "credential stuffing",
    )

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

    def _platforms(self, doc):

        platforms = doc.get("platforms") or []

        if isinstance(platforms, str):
            platforms = [platforms]

        return set(platforms)

    def is_iot_relevant(self, doc):

        platforms = self._platforms(doc)

        if platforms & self.KEEP_PLATFORMS:
            return True

        text = (
            f"{doc.get('name', '')} "
            f"{doc.get('description', '')} "
            f"{doc.get('detection', '')}"
        ).lower()

        return any(keyword in text for keyword in self.IOT_KEYWORDS)

    def filter_iot_relevant(self, documents):
        """Reduce Enterprise ATT&CK noise for IoT cybersecurity RAG."""

        return [
            doc for doc in documents
            if self.is_iot_relevant(doc)
        ]
