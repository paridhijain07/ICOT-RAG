import json
import sys

sys.path.insert(0, ".")

from rag_icot.components.text_cleaner import TextCleaner
from rag_icot.components.variot_knowledge_builder import VARIoTKnowledgeBuilder
from rag_icot.components.variot_exploits_knowledge_builder import (
    VARIoTExploitKnowledgeBuilder,
)
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder


def main():
    kb = KnowledgeBaseBuilder()
    cleaner = TextCleaner()

    raw_vulns = json.load(
        open("artifacts/variot_vulnerabilities.json", encoding="utf-8")
    )
    raw_exploits = json.load(
        open("artifacts/variot_exploits.json", encoding="utf-8")
    )

    print("RAW vulns", len(raw_vulns), "exploits", len(raw_exploits), flush=True)
    print("raw vuln title type", type(raw_vulns[0].get("title")), flush=True)

    vuln_knowledge = VARIoTKnowledgeBuilder().build(raw_vulns)
    exploit_knowledge = VARIoTExploitKnowledgeBuilder().build(raw_exploits)

    print(
        "BUILT vulns",
        len(vuln_knowledge),
        "exploits",
        len(exploit_knowledge),
        flush=True,
    )
    print("sample vuln title:", vuln_knowledge[0]["title"][:80], flush=True)
    print(
        "sample vuln desc len:",
        len(vuln_knowledge[0]["description"]),
        flush=True,
    )
    assert isinstance(vuln_knowledge[0]["title"], str)
    assert "{" not in vuln_knowledge[0]["title"]
    assert len(vuln_knowledge) == len(raw_vulns) or len(vuln_knowledge) > 0

    kb.save_documents(vuln_knowledge, "artifacts/variot_knowledge.json")
    kb.save_documents(
        exploit_knowledge, "artifacts/variot_exploit_knowledge.json"
    )

    cleaned_vulns = []
    for v in raw_vulns:
        cleaned_vulns.append(
            {
                "variot_id": v.get("variot_id") or v.get("id"),
                "cve": v.get("cve") or "",
                "title": cleaner.clean(v.get("title"), max_length=300),
                "description": cleaner.clean(
                    v.get("description"), max_length=3000
                ),
                "threat_type": cleaner.extract_field(v.get("threat_type")),
                "document_type": "vulnerability",
            }
        )
    kb.save_documents(cleaned_vulns, "artifacts/variot_vulnerabilities.json")
    print("VARIoT rebuild complete", flush=True)


if __name__ == "__main__":
    main()
