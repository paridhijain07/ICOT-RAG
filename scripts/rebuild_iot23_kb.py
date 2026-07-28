import os
import sys

sys.path.insert(0, ".")

from rag_icot.components.data_ingestion import DataIngestion
from rag_icot.components.iot23_knowledge_builder import IoT23KnowledgeBuilder
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder


def main():
    ingestion = DataIngestion()
    builder = IoT23KnowledgeBuilder()
    kb = KnowledgeBaseBuilder()

    dataset_folder = "datasets/iot23"
    scenario_stats = {}

    for folder in sorted(os.listdir(dataset_folder)):
        scenario_path = os.path.join(
            dataset_folder,
            folder,
            "bro",
            "conn.log.labeled",
        )

        if not os.path.exists(scenario_path):
            print(f"SKIP missing log: {folder}", flush=True)
            continue

        print(f"Aggregating {folder} ...", flush=True)
        stats = ingestion.aggregate_iot23_scenario(scenario_path)
        scenario_stats[folder] = stats
        print(
            f"  flows={stats['flow_count']} "
            f"labels={list(stats['label_counts'].keys())[:5]}",
            flush=True,
        )

    docs = builder.build_from_stats(scenario_stats, include_benign=True)
    print("TOTAL IoT23 docs", len(docs), flush=True)

    for d in docs:
        print(
            f"  {d['malware_family']:20} | {d['scenario']} | "
            f"flows={d['flow_count']}",
            flush=True,
        )

    mirai = [d for d in docs if "mirai" in d["malware_family"].lower()]
    print("Mirai docs", len(mirai), flush=True)
    if mirai:
        print("Mirai preview:", mirai[0]["summary"][:300], flush=True)

    kb.save_documents(docs, "artifacts/iot23_knowledge.json")
    print("Saved artifacts/iot23_knowledge.json", flush=True)


if __name__ == "__main__":
    main()
