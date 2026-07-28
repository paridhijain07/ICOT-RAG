import pandas as pd


class IoT23KnowledgeBuilder:
    """Build searchable IoT-23 documents from labeled traffic.

    Creates one narrative document per scenario (preferred), using the
    official IoT-23 malware/device mapping so queries like "Mirai" can match.
    """

    # Official Aposemat IoT-23 scenario mapping
    SCENARIO_MALWARE = {
        "CTU-IoT-Malware-Capture-1-1": "Hide and Seek",
        "CTU-IoT-Malware-Capture-3-1": "Muhstik",
        "CTU-IoT-Malware-Capture-7-1": "Mirai",
        "CTU-IoT-Malware-Capture-8-1": "Hakai",
        "CTU-IoT-Malware-Capture-9-1": "Hajime",
        "CTU-IoT-Malware-Capture-17-1": "Kenjiro",
        "CTU-IoT-Malware-Capture-20-1": "Torii",
        "CTU-IoT-Malware-Capture-21-1": "Torii",
        "CTU-IoT-Malware-Capture-33-1": "Kenjiro",
        "CTU-IoT-Malware-Capture-34-1": "Mirai",
        "CTU-IoT-Malware-Capture-35-1": "Mirai",
        "CTU-IoT-Malware-Capture-36-1": "Okiru",
        "CTU-IoT-Malware-Capture-39-1": "IRCBot",
        "CTU-IoT-Malware-Capture-42-1": "Trojan",
        "CTU-IoT-Malware-Capture-43-1": "Mirai",
        "CTU-IoT-Malware-Capture-44-1": "Mirai",
        "CTU-IoT-Malware-Capture-48-1": "Mirai",
        "CTU-IoT-Malware-Capture-49-1": "Mirai",
        "CTU-IoT-Malware-Capture-52-1": "Mirai",
        "CTU-IoT-Malware-Capture-60-1": "Gagfyt",
        "CTU-Honeypot-Capture-4-1": "Benign Philips HUE",
        "CTU-Honeypot-Capture-5-1": "Benign Amazon Echo",
        "CTU-Honeypot-Capture-7-1": "Benign Somfy Doorlock",
    }

    IGNORED_LABELS = {"-", "", "benign"}

    def __init__(self):
        pass

    def _behavior_counts_from_labels(self, label_counts):

        return {
            label: int(count)
            for label, count in label_counts.items()
            if str(label).lower() not in self.IGNORED_LABELS
        }

    def _document_from_stats(
        self,
        scenario,
        stats,
        include_benign=True
    ):

        malware_family = self.SCENARIO_MALWARE.get(
            scenario,
            "Unknown IoT malware"
        )

        if (
            not include_benign
            and malware_family.lower().startswith("benign")
        ):
            return None

        behavior_counts = self._behavior_counts_from_labels(
            stats.get("label_counts", {})
        )

        protocol_distribution = {
            str(k): int(v)
            for k, v in stats.get("protocol_distribution", {}).items()
        }

        service_distribution = {
            str(k): int(v)
            for k, v in stats.get("service_distribution", {}).items()
        }

        flow_count = int(stats.get("flow_count", 0))
        protocol = (
            max(protocol_distribution, key=protocol_distribution.get)
            if protocol_distribution else "unknown"
        )
        service = (
            max(service_distribution, key=service_distribution.get)
            if service_distribution else "unknown"
        )

        if behavior_counts:
            behaviors = ", ".join(
                f"{label} ({count} flows)"
                for label, count in sorted(
                    behavior_counts.items(),
                    key=lambda item: item[1],
                    reverse=True
                )[:8]
            )
        else:
            behaviors = "no malicious detailed-labels observed"

        is_benign = malware_family.lower().startswith("benign")

        if is_benign:
            summary = (
                f"IoT-23 scenario {scenario} contains benign traffic from "
                f"{malware_family.replace('Benign ', '')}. "
                f"It includes {flow_count} network flows, primarily using "
                f"the {protocol.upper()} protocol. "
                f"Most common service: {service}."
            )
        else:
            summary = (
                f"IoT-23 scenario {scenario} involves {malware_family} "
                f"malware infecting an IoT device. "
                f"Observed network behaviours include: {behaviors}. "
                f"The capture contains {flow_count} flows, primarily "
                f"{protocol.upper()} traffic. "
                f"Most common service: {service}. "
                f"This evidence describes {malware_family} botnet/malware "
                f"behaviour including scanning, command-and-control, "
                f"or denial-of-service activity when present in labels."
            )

        scenario_slug = scenario.lower().replace(" ", "_")

        return {
            "id": f"iot23_{scenario_slug}",
            "source": "IoT23",
            "document_type": "traffic_behaviour",
            "scenario": scenario,
            "malware_family": malware_family,
            "attack_type": malware_family,
            "behaviours": behavior_counts,
            "title": f"{malware_family} — {scenario}",
            "description": summary,
            "summary": summary,
            "flow_count": flow_count,
            "protocol_distribution": protocol_distribution,
            "service_distribution": service_distribution,
            "average_duration": float(
                stats.get("average_duration", 0.0)
            ),
            "unique_source_ips": int(
                stats.get("unique_source_ips", 0)
            ),
            "unique_destination_ips": int(
                stats.get("unique_destination_ips", 0)
            ),
        }

    def build_from_stats(
        self,
        scenario_stats,
        include_benign=True
    ):
        """Build docs from streaming aggregates: {scenario: stats_dict}."""

        knowledge_documents = []

        for scenario in sorted(scenario_stats.keys()):
            document = self._document_from_stats(
                scenario,
                scenario_stats[scenario],
                include_benign=include_benign
            )

            if document is not None:
                knowledge_documents.append(document)

        return knowledge_documents

    def build(self, df, include_benign=True):
        """Build one knowledge document per IoT-23 scenario from a DataFrame."""

        scenario_stats = {}

        for scenario in sorted(df["scenario"].unique()):
            scenario_df = df[df["scenario"] == scenario]

            scenario_stats[scenario] = {
                "flow_count": len(scenario_df),
                "protocol_distribution": (
                    scenario_df["proto"].value_counts().to_dict()
                ),
                "service_distribution": (
                    scenario_df["service"].value_counts().to_dict()
                ),
                "label_counts": (
                    scenario_df["detailed-label"]
                    .fillna("-")
                    .astype(str)
                    .value_counts()
                    .to_dict()
                ),
                "average_duration": float(
                    round(
                        pd.to_numeric(
                            scenario_df["duration"],
                            errors="coerce"
                        )
                        .fillna(0)
                        .mean(),
                        4
                    )
                ),
                "unique_source_ips": int(
                    scenario_df["id.orig_h"].nunique()
                ),
                "unique_destination_ips": int(
                    scenario_df["id.resp_h"].nunique()
                ),
            }

        return self.build_from_stats(
            scenario_stats,
            include_benign=include_benign
        )

    def build_by_label(self, df):
        """Legacy label-aggregated docs (kept for compatibility)."""

        knowledge_documents = []

        attack_types = sorted(df["detailed-label"].unique())

        for attack in attack_types:

            if str(attack).lower() in self.IGNORED_LABELS:
                continue

            attack_df = df[df["detailed-label"] == attack]

            flow_count = len(attack_df)

            protocol_distribution = (
                attack_df["proto"]
                .value_counts()
                .to_dict()
            )

            service_distribution = (
                attack_df["service"]
                .value_counts()
                .to_dict()
            )

            scenarios = (
                attack_df["scenario"]
                .unique()
                .tolist()
            )

            families = sorted({
                self.SCENARIO_MALWARE.get(scenario, "Unknown")
                for scenario in scenarios
            })

            most_common_protocol = max(
                protocol_distribution,
                key=protocol_distribution.get
            )

            most_common_service = max(
                service_distribution,
                key=service_distribution.get
            )

            summary = (
                f"IoT-23 behaviour label '{attack}' was observed in "
                f"{len(scenarios)} scenario(s) linked to malware families "
                f"{', '.join(families)}. "
                f"It consists of {flow_count} network flows, primarily "
                f"using {most_common_protocol.upper()}. "
                f"Most common service: {most_common_service}."
            )

            document = {
                "id": (
                    f'iot23_label_'
                    f'{str(attack).lower().replace(" ", "_").replace("&", "and")}'
                ),
                "source": "IoT23",
                "document_type": "traffic_behaviour_label",
                "attack_type": attack,
                "malware_families": families,
                "title": f"IoT-23 behaviour: {attack}",
                "description": summary,
                "summary": summary,
                "flow_count": int(flow_count),
                "protocol_distribution": {
                    str(k): int(v)
                    for k, v in protocol_distribution.items()
                },
                "service_distribution": {
                    str(k): int(v)
                    for k, v in service_distribution.items()
                },
                "scenarios": scenarios,
            }

            knowledge_documents.append(document)

        return knowledge_documents
