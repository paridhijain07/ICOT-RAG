"""Fetch a larger VARIoT sample, rebuild knowledge, remaster index."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_icot.components.embedding_builder import EmbeddingBuilder
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder
from rag_icot.components.mitre_knowledge_builder import MITREKnowledgeBuilder
from rag_icot.components.variot_exploits_knowledge_builder import (
    VARIoTExploitKnowledgeBuilder,
)
from rag_icot.components.variot_knowledge_builder import VARIoTKnowledgeBuilder
from rag_icot.components.variot_loader import VARIoTLoader
from rag_icot.components.vector_store import VectorStore


def main(
    max_vulns=500,
    max_exploits=500,
):
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"
    kb = KnowledgeBaseBuilder()
    loader = VARIoTLoader()

    print(
        f"Fetching VARIoT vulns (max={max_vulns})...",
        flush=True,
    )
    vulns = loader.get_vulnerabilities(
        limit=100,
        max_records=max_vulns,
        normalize=True,
    )
    print(f"Fetched vulns: {len(vulns)}", flush=True)

    print(
        f"Fetching VARIoT exploits (max={max_exploits})...",
        flush=True,
    )
    exploits = loader.get_exploits(
        limit=100,
        max_records=max_exploits,
        normalize=True,
    )
    print(f"Fetched exploits: {len(exploits)}", flush=True)

    kb.save_documents(vulns, str(artifacts / "variot_vulnerabilities.json"))
    kb.save_documents(exploits, str(artifacts / "variot_exploits.json"))

    vuln_knowledge = VARIoTKnowledgeBuilder().build(vulns)
    exploit_knowledge = VARIoTExploitKnowledgeBuilder().build(exploits)

    kb.save_documents(
        vuln_knowledge,
        str(artifacts / "variot_knowledge.json"),
    )
    kb.save_documents(
        exploit_knowledge,
        str(artifacts / "variot_exploit_knowledge.json"),
    )

    print(
        f"Knowledge vulns={len(vuln_knowledge)} "
        f"exploits={len(exploit_knowledge)}",
        flush=True,
    )

    mirai_v = sum(
        1
        for d in vuln_knowledge
        if "mirai" in json.dumps(d).lower()
    )
    mirai_e = sum(
        1
        for d in exploit_knowledge
        if "mirai" in json.dumps(d).lower()
    )
    print(f"Mirai mentions: vulns={mirai_v} exploits={mirai_e}", flush=True)

    # Remaster with filtered MITRE + IoT23
    mitre_all = kb.load_documents(str(artifacts / "mitre_knowledge.json"))
    mitre = MITREKnowledgeBuilder().filter_iot_relevant(mitre_all)
    iot23 = kb.load_documents(str(artifacts / "iot23_knowledge.json"))

    master = kb.merge_documents(
        mitre,
        vuln_knowledge,
        exploit_knowledge,
        iot23,
    )
    print(f"MASTER total: {len(master)}", flush=True)
    print(
        "Sources:",
        dict(Counter(d.get("source") for d in master)),
        flush=True,
    )
    kb.save_documents(master, str(artifacts / "master_documents.json"))
    kb.save_documents(
        mitre,
        str(artifacts / "mitre_knowledge_filtered.json"),
    )

    print("Embedding...", flush=True)
    embedder = EmbeddingBuilder()
    embeddings = embedder.embed_documents(master)
    embedder.save_embeddings(
        embeddings,
        str(artifacts / "master_embeddings.npy"),
    )

    print("Rebuilding Chroma...", flush=True)
    store = VectorStore(persist_directory=str(artifacts / "chroma_db"))
    store.create_collection("icot_knowledge")
    store.add_documents(master, embeddings)
    print(f"Chroma count: {store.collection.count()}", flush=True)

    query = "Mirai botnet infection vectors vulnerabilities mitigations"
    results = store.search(embedder.embed(query), k=8)
    print("Top retrieval for Mirai query:", flush=True)
    for i, (doc_id, text, meta) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        )
    ):
        preview = (text or "")[:140].replace("\n", " ")
        print(
            f"[{i+1}] {doc_id} | {meta.get('source')} | {preview}...",
            flush=True,
        )

    print("Done.", flush=True)


if __name__ == "__main__":
    main()
