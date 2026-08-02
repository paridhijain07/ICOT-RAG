"""Rebuild IoT-23 scenario (+ family) knowledge from datasets/iot23.

Resume-safe: caches per-scenario aggregates under
artifacts/iot23_scenario_stats.json so multi-GB captures are not
re-scanned unless --force is set.

Examples:
  python scripts/rebuild_iot23_kb.py
  python scripts/rebuild_iot23_kb.py --force
  python scripts/rebuild_iot23_kb.py --only CTU-IoT-Malware-Capture-34-1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_icot.components.data_ingestion import DataIngestion
from rag_icot.components.iot23_knowledge_builder import IoT23KnowledgeBuilder
from rag_icot.components.knowledge_base_builder import KnowledgeBaseBuilder

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "iot23"
STATS_PATH = ROOT / "artifacts" / "iot23_scenario_stats.json"
OUT_PATH = ROOT / "artifacts" / "iot23_knowledge.json"
OLD_KB_PATH = ROOT / "artifacts" / "iot23_knowledge.json"


def _stats_from_existing_doc(doc: dict) -> dict:
    """Recover aggregate stats from a previously built scenario document."""

    return {
        "flow_count": int(doc.get("flow_count") or 0),
        "protocol_distribution": dict(doc.get("protocol_distribution") or {}),
        "service_distribution": dict(doc.get("service_distribution") or {}),
        "label_counts": dict(doc.get("behaviours") or {}),
        "average_duration": float(doc.get("average_duration") or 0.0),
        "unique_source_ips": int(doc.get("unique_source_ips") or 0),
        "unique_destination_ips": int(doc.get("unique_destination_ips") or 0),
        "from_existing_doc": True,
    }


def _load_stats_cache() -> dict:
    if not STATS_PATH.exists():
        return {}
    return json.loads(STATS_PATH.read_text(encoding="utf-8"))


def _save_stats_cache(stats: dict) -> None:
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-aggregate scenarios even if cached stats exist",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Only process these scenario folder names (repeatable)",
    )
    parser.add_argument(
        "--no-family-rollups",
        action="store_true",
        help="Skip family-level summary documents",
    )
    args = parser.parse_args()

    ingestion = DataIngestion()
    builder = IoT23KnowledgeBuilder()
    kb = KnowledgeBaseBuilder()

    folders = sorted(
        p.name for p in DATASET.iterdir() if p.is_dir()
    )
    if args.only:
        only = set(args.only)
        folders = [f for f in folders if f in only]

    scenario_stats = _load_stats_cache()

    # Seed cache from previous KB docs when stats are missing (avoid re-scan)
    if OLD_KB_PATH.exists() and not args.force:
        old_docs = json.loads(OLD_KB_PATH.read_text(encoding="utf-8"))
        for doc in old_docs:
            if doc.get("document_type") != "traffic_behaviour":
                continue
            scenario = doc.get("scenario")
            if scenario and scenario not in scenario_stats:
                scenario_stats[scenario] = _stats_from_existing_doc(doc)

    print(f"Scenarios on disk: {len(folders)}", flush=True)
    print(f"Cached stats: {len(scenario_stats)}", flush=True)

    for folder in folders:
        log_path = ingestion.find_iot23_labeled_log(DATASET / folder)
        if not log_path:
            print(f"SKIP missing log: {folder}", flush=True)
            continue

        if not args.force and folder in scenario_stats:
            print(
                f"Reuse cached stats: {folder} "
                f"(flows={scenario_stats[folder].get('flow_count')})",
                flush=True,
            )
            continue

        size_mb = os.path.getsize(log_path) / (1024 * 1024)
        print(
            f"Aggregating {folder} ({size_mb:.1f} MB) ...",
            flush=True,
        )
        print(f"  log: {log_path}", flush=True)
        stats = ingestion.aggregate_iot23_scenario(log_path)
        scenario_stats[folder] = stats
        _save_stats_cache(scenario_stats)
        labels = list(stats["label_counts"].keys())[:6]
        print(
            f"  flows={stats['flow_count']} labels={labels}",
            flush=True,
        )

    # Keep stats only for scenario folders that still exist on disk.
    # Full KB is rebuilt from the full cache so --only can fill gaps.
    active = {
        k: v
        for k, v in scenario_stats.items()
        if (DATASET / k).is_dir()
    }
    _save_stats_cache(active)

    docs = builder.build_from_stats(active, include_benign=True)
    family_docs = []
    if not args.no_family_rollups:
        family_docs = builder.build_family_summaries(docs)
        docs = docs + family_docs

    print("TOTAL IoT23 docs", len(docs), flush=True)
    print(
        f"  scenario={len(docs) - len(family_docs)} "
        f"family_rollups={len(family_docs)}",
        flush=True,
    )

    for d in docs:
        print(
            f"  {str(d.get('malware_family', '')):22} | "
            f"{d.get('document_type')} | "
            f"{d.get('scenario', '')[:48]} | "
            f"flows={d.get('flow_count')}",
            flush=True,
        )

    mirai = [
        d for d in docs
        if "mirai" in str(d.get("malware_family", "")).lower()
    ]
    print("Mirai docs", len(mirai), flush=True)
    if mirai:
        print("Mirai preview:", mirai[0]["summary"][:280], flush=True)

    kb.save_documents(docs, str(OUT_PATH))
    print(f"Saved {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
