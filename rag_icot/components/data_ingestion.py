import os
from collections import Counter
from pathlib import Path

import pandas as pd


class DataIngestion:

    def _parse_fields_header(self, file_path):

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#fields"):
                    fields = line.strip().split("\t")[1:]
                    last_field = fields.pop()
                    fields.extend(last_field.split())
                    return fields

        raise ValueError(f"No #fields header found in {file_path}")

    def _parse_row(self, line, expected_cols):

        parts = line.strip().split("\t")
        last_field = parts.pop()
        parts.extend(last_field.split())

        # Zeek labeled logs append tunnel_parents/label/detailed-label
        if len(parts) < expected_cols:
            parts.extend(["-"] * (expected_cols - len(parts)))

        return parts[:expected_cols]

    def load_iot23(self, file_path):

        columns = self._parse_fields_header(file_path)
        rows = []

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#"):
                    continue

                rows.append(
                    self._parse_row(line, len(columns))
                )

        return pd.DataFrame(rows, columns=columns)

    def aggregate_iot23_scenario(self, file_path):
        """Stream a labeled conn.log and return compact scenario stats.

        Avoids loading multi-million-row captures fully into memory.
        """

        columns = self._parse_fields_header(file_path)

        idx = {
            name: columns.index(name)
            for name in [
                "proto",
                "service",
                "duration",
                "id.orig_h",
                "id.resp_h",
                "detailed-label",
            ]
            if name in columns
        }

        required = [
            "proto",
            "service",
            "detailed-label",
        ]

        for name in required:
            if name not in idx:
                raise ValueError(
                    f"Missing column '{name}' in {file_path}"
                )

        proto_counts = Counter()
        service_counts = Counter()
        label_counts = Counter()
        source_ips = set()
        dest_ips = set()

        flow_count = 0
        duration_sum = 0.0
        duration_n = 0

        # Cap unique-IP tracking for very large files
        max_tracked_ips = 50000

        progress_every = 1_000_000

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#"):
                    continue

                parts = self._parse_row(line, len(columns))
                flow_count += 1

                if flow_count % progress_every == 0:
                    print(
                        f"    ... {flow_count:,} flows",
                        flush=True,
                    )

                proto_counts[parts[idx["proto"]]] += 1
                service_counts[parts[idx["service"]]] += 1
                label_counts[parts[idx["detailed-label"]]] += 1

                if "duration" in idx:
                    try:
                        duration_sum += float(parts[idx["duration"]])
                        duration_n += 1
                    except ValueError:
                        pass

                if len(source_ips) < max_tracked_ips and "id.orig_h" in idx:
                    source_ips.add(parts[idx["id.orig_h"]])

                if len(dest_ips) < max_tracked_ips and "id.resp_h" in idx:
                    dest_ips.add(parts[idx["id.resp_h"]])

        avg_duration = (
            duration_sum / duration_n
            if duration_n
            else 0.0
        )

        return {
            "flow_count": flow_count,
            "protocol_distribution": dict(proto_counts),
            "service_distribution": dict(service_counts),
            "label_counts": dict(label_counts),
            "average_duration": float(round(avg_duration, 4)),
            "unique_source_ips": len(source_ips),
            "unique_destination_ips": len(dest_ips),
        }

    @staticmethod
    def find_iot23_labeled_log(scenario_dir):
        """Locate conn.log.labeled under a scenario folder.

        Handles both ``bro/conn.log.labeled`` and nested layouts
        (e.g. honeypot captures with ``Somfy-01/bro/...``).
        """

        scenario_dir = Path(scenario_dir)
        direct = scenario_dir / "bro" / "conn.log.labeled"
        if direct.is_file():
            return str(direct)

        matches = sorted(scenario_dir.rglob("conn.log.labeled"))
        if not matches:
            return None
        # Prefer a path that still sits under a bro/ directory
        for path in matches:
            if path.parent.name == "bro":
                return str(path)
        return str(matches[0])

    def load_all_iot23(self, dataset_folder):

        all_data = []

        for folder in os.listdir(dataset_folder):

            scenario_path = self.find_iot23_labeled_log(
                os.path.join(dataset_folder, folder)
            )

            if scenario_path:

                print(f"Loading {folder}")

                df = self.load_iot23(scenario_path)

                df["scenario"] = folder

                all_data.append(df)

        combined_df = pd.concat(
            all_data,
            ignore_index=True
        )

        return combined_df