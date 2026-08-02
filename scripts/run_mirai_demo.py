import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.environ["PYTHONIOENCODING"] = "utf-8"

from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline


def main():
    question = (
        "How does Mirai infect IoT devices, and what mitigations "
        "and related vulnerabilities should I know about?"
    )
    print("QUESTION:", question, flush=True)

    pipeline = RAGICOTPipeline()
    result = pipeline.run(question, max_iterations=3)

    print("\nCOVERED FACETS:", result.get("covered_facets"), flush=True)
    print("\nTRACE SUMMARY", flush=True)
    for step in result["trace"]:
        print(
            f"Iter {step['iteration']}: enough={step['enough_information']} "
            f"missing_facets={step.get('missing_facets')} "
            f"next_source={step.get('next_source')} "
            f"query={step.get('search_query')!r}",
            flush=True,
        )

    print(f"\nDOCS: {len(result['documents'])}", flush=True)
    for i, doc in enumerate(result["documents"]):
        meta = doc.get("metadata") or {}
        print(
            f"[{i+1}] {doc['id']} | {meta.get('source')} | "
            f"{meta.get('document_type') or meta.get('malware_family') or meta.get('name') or ''}",
            flush=True,
        )

    print("\nANSWER PREVIEW:\n", flush=True)
    print(result["answer"][:2000], flush=True)

    out = root / "artifacts" / "mirai_demo_output.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("\nSaved", out, flush=True)


if __name__ == "__main__":
    main()
