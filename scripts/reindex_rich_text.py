"""Rebuild VARIoT knowledge with product enrichment, then remaster + reindex.

Does not re-fetch from VARIoT API — uses local raw JSON artifacts.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_icot.components.document_text import build_document_text
from rag_icot.components.embedding_builder import EmbeddingBuilder
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder
from rag_icot.components.mitre_knowledge_builder import MITREKnowledgeBuilder
from rag_icot.components.variot_exploits_knowledge_builder import (
    VARIoTExploitKnowledgeBuilder,
)
from rag_icot.components.variot_knowledge_builder import VARIoTKnowledgeBuilder
from rag_icot.components.vector_store import VectorStore


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"
    kb = KnowledgeBaseBuilder()

    print("Rebuilding VARIoT knowledge (offline)...", flush=True)
    raw_vulns = kb.load_documents(str(artifacts / "variot_vulnerabilities.json"))
    raw_exploits = kb.load_documents(str(artifacts / "variot_exploits.json"))

    vuln_knowledge = VARIoTKnowledgeBuilder().build(raw_vulns)
    exploit_knowledge = VARIoTExploitKnowledgeBuilder().build(raw_exploits)

    with_products = sum(
        1 for d in vuln_knowledge if d.get("affected_products")
    )
    print(
        f"Vulns={len(vuln_knowledge)} with_products={with_products} "
        f"exploits={len(exploit_knowledge)}",
        flush=True,
    )

    sample = next(
        d for d in vuln_knowledge if d.get("cve") == "CVE-2020-8863"
    )
    print("Sample CVE-2020-8863 products:", sample.get("affected_products"))
    print("Sample embed text preview:")
    print(build_document_text({**sample, "source": "VARIoT"})[:350])
    print(flush=True)

    kb.save_documents(vuln_knowledge, str(artifacts / "variot_knowledge.json"))
    kb.save_documents(
        exploit_knowledge,
        str(artifacts / "variot_exploit_knowledge.json"),
    )

    print("Merging master KB...", flush=True)
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
    print("Sources:", dict(Counter(d.get("source") for d in master)), flush=True)
    kb.save_documents(master, str(artifacts / "master_documents.json"))

    print("Embedding documents...", flush=True)
    embedder = EmbeddingBuilder()
    embeddings = embedder.embed_documents(master)
    embedder.save_embeddings(
        embeddings,
        str(artifacts / "master_embeddings.npy"),
    )
    print(f"Embeddings shape: {embeddings.shape}", flush=True)

    print("Rebuilding ChromaDB...", flush=True)
    store = VectorStore(persist_directory=str(artifacts / "chroma_db"))
    store.create_collection("icot_knowledge")
    store.add_documents(master, embeddings)
    print(f"Chroma count: {store.collection.count()}", flush=True)

    print("Smoke-testing CVE-2020-8863 retrieval...", flush=True)
    query = "What is CVE-2020-8863 about and which products are affected?"
    results = store.search(embedder.embed(query), k=5)
    for i, (doc_id, text, meta) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        ),
        start=1,
    ):
        preview = (text or "")[:120].replace("\n", " | ")
        print(
            f"[{i}] {doc_id} | cve={meta.get('cve')} | {preview}",
            flush=True,
        )

    top_ids = results["ids"][0]
    if "variot_vuln_434" in top_ids[:3]:
        print("PASS: CVE-2020-8863 doc in top-3", flush=True)
    else:
        print("WARN: expected variot_vuln_434 in top-3", flush=True)
        print("top_ids:", top_ids, flush=True)

    print("Smoke-testing Mirai retrieval...", flush=True)
    mirai_q = (
        "What network behaviours does Mirai show in the "
        "IoT-23 Capture-7-1 scenario?"
    )
    mirai_res = store.search(embedder.embed(mirai_q), k=3)
    print("Mirai top:", mirai_res["ids"][0], flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
