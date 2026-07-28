"""Diagnose KB retrieval for smoke eval questions (no secrets)."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])

from rag_icot.components.retriever import Retriever


def show_hits(label: str, question: str, k: int = 10) -> None:
    print("=" * 80)
    print(label)
    print(question)
    print("=" * 80)

    retriever = Retriever()
    res = retriever.retrieve(question, k=k)
    print("collection_count", retriever.vector_store.collection.count())

    for i, (doc_id, doc, meta, dist) in enumerate(
        zip(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ),
        start=1,
    ):
        meta = meta or {}
        text = doc or ""
        print(
            f"{i:2d} dist={dist:.4f} id={doc_id} "
            f"src={meta.get('source')} type={meta.get('document_type')} "
            f"cve={meta.get('cve')} family={meta.get('malware_family')}"
        )
        print("   title:", (meta.get("title") or meta.get("name") or "")[:70])
        print("   has_cve_token:", "CVE-2020-8863" in text)
        print("   text:", text[:140].replace("\n", " "))


def inspect_cve_doc() -> None:
    docs = json.loads(
        Path("artifacts/master_documents.json").read_text(encoding="utf-8")
    )
    doc = next(d for d in docs if d["id"] == "variot_vuln_434")
    desc = doc.get("description") or ""
    idx = desc.upper().find("CVE-2020-8863")
    print("=" * 80)
    print("variot_vuln_434 CVE position in description:", idx)
    print("affected_products:", doc.get("affected_products"))
    print("snippet around CVE:", repr(desc[max(0, idx - 40) : idx + 60]))


if __name__ == "__main__":
    inspect_cve_doc()
    show_hits(
        "q011",
        "What is CVE-2020-8863 about and which products are affected?",
        k=10,
    )
    show_hits(
        "q001",
        "What network behaviours does Mirai show in the IoT-23 Capture-7-1 scenario?",
        k=5,
    )
