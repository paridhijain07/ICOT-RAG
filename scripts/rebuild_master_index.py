"""Filter MITRE, merge master KB, rebuild embeddings + Chroma index."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_icot.components.embedding_builder import EmbeddingBuilder
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder
from rag_icot.components.mitre_knowledge_builder import MITREKnowledgeBuilder
from rag_icot.components.vector_store import VectorStore


def main():
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"

    kb = KnowledgeBaseBuilder()
    mitre_builder = MITREKnowledgeBuilder()

    print("Loading source knowledge...", flush=True)
    mitre_all = kb.load_documents(str(artifacts / "mitre_knowledge.json"))
    variot = kb.load_documents(str(artifacts / "variot_knowledge.json"))
    exploits = kb.load_documents(
        str(artifacts / "variot_exploit_knowledge.json")
    )
    iot23 = kb.load_documents(str(artifacts / "iot23_knowledge.json"))

    mitre = mitre_builder.filter_iot_relevant(mitre_all)
    kb.save_documents(
        mitre,
        str(artifacts / "mitre_knowledge_filtered.json")
    )

    print(
        f"MITRE: {len(mitre_all)} -> filtered {len(mitre)}",
        flush=True,
    )
    print(f"VARIoT vulns: {len(variot)}", flush=True)
    print(f"VARIoT exploits: {len(exploits)}", flush=True)
    print(f"IoT23: {len(iot23)}", flush=True)

    master = kb.merge_documents(mitre, variot, exploits, iot23)
    print(f"MASTER total: {len(master)}", flush=True)
    print(
        "Sources:",
        dict(Counter(d.get("source") for d in master)),
        flush=True,
    )

    mirai_hits = [
        d for d in master
        if "mirai" in json.dumps(d).lower()
    ]
    print(f"Docs mentioning Mirai: {len(mirai_hits)}", flush=True)
    for d in mirai_hits[:5]:
        print(f"  - {d.get('id')} | {d.get('title') or d.get('name')}", flush=True)

    kb.save_documents(master, str(artifacts / "master_documents.json"))

    print("Embedding documents...", flush=True)
    embedder = EmbeddingBuilder()
    embeddings = embedder.embed_documents(master)
    embedder.save_embeddings(
        embeddings,
        str(artifacts / "master_embeddings.npy")
    )
    print(f"Embeddings shape: {embeddings.shape}", flush=True)

    print("Rebuilding ChromaDB...", flush=True)
    store = VectorStore(persist_directory=str(artifacts / "chroma_db"))
    store.create_collection("icot_knowledge")
    store.add_documents(master, embeddings)
    print(
        f"Chroma count: {store.collection.count()}",
        flush=True,
    )

    print("Smoke-testing Mirai retrieval...", flush=True)
    query = (
        "How does Mirai infect IoT devices, and what mitigations "
        "and related vulnerabilities should I know about?"
    )
    q_emb = embedder.embed(query)
    results = store.search(q_emb, k=5)

    for i, (doc_id, text, meta) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        )
    ):
        preview = (text or "")[:160].replace("\n", " ")
        print(
            f"[{i+1}] {doc_id} | source={meta.get('source')} | {preview}...",
            flush=True,
        )

    print("Done.", flush=True)


if __name__ == "__main__":
    main()
