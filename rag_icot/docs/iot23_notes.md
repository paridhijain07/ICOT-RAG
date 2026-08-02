# IoT-23 knowledge notes

## Dataset purpose

Network traffic evidence for IoT malware / honeypot behaviour (Aposemat IoT-23).

## Layout expected under `datasets/iot23/`

Each scenario folder should contain a Zeek/Bro labeled connection log:

- Preferred: `bro/conn.log.labeled`
- Also accepted: nested paths such as `Somfy-01/bro/conn.log.labeled`

Rebuild discovers logs via `DataIngestion.find_iot23_labeled_log`.

## Rebuild

```bash
# Aggregate new/missing scenarios (resume-safe; caches stats)
python scripts/rebuild_iot23_kb.py

# Then merge + re-embed + Chroma
python scripts/rebuild_master_index.py
```

Outputs:

- `artifacts/iot23_scenario_stats.json` — per-scenario aggregates (resume cache)
- `artifacts/iot23_knowledge.json` — scenario docs + family rollups
- Master index via `rebuild_master_index.py`

## Document types

| Type | Meaning |
|------|---------|
| `traffic_behaviour` | One doc per capture/scenario |
| `traffic_behaviour_family` | Rollup when a family appears in ≥2 scenarios (e.g. Mirai) |

## Use in project

Provides real attack-traffic behaviour evidence for the `behaviour` facet (source `IoT23`).
