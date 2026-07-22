import pandas as pd


class IoT23KnowledgeBuilder:

    def __init__(self):
        pass

    def build(self, df):

        knowledge_documents = []

        attack_types = sorted(df["detailed-label"].unique())

        for attack in attack_types:

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

            connection_state_distribution = (
                attack_df["conn_state"]
                .value_counts()
                .to_dict()
            )

            avg_duration = (
                pd.to_numeric(
                    attack_df["duration"],
                    errors="coerce"
                )
                .fillna(0)
                .mean()
            )

            avg_orig_bytes = (
                pd.to_numeric(
                    attack_df["orig_bytes"],
                    errors="coerce"
                )
                .fillna(0)
                .mean()
            )

            avg_resp_bytes = (
                pd.to_numeric(
                    attack_df["resp_bytes"],
                    errors="coerce"
                )
                .fillna(0)
                .mean()
            )

            unique_source_ips = (
                attack_df["id.orig_h"]
                .nunique()
            )

            unique_destination_ips = (
                attack_df["id.resp_h"]
                .nunique()
            )

            scenarios = (
                attack_df["scenario"]
                .unique()
                .tolist()
            )

            most_common_protocol = max(
                protocol_distribution,
                key=protocol_distribution.get
            )

            most_common_service = max(
                service_distribution,
                key=service_distribution.get
            )

            summary = (
                f"{attack} consists of {flow_count} network flows. "
                f"It primarily uses the {most_common_protocol.upper()} protocol. "
                f"The most common service is {most_common_service}. "
                f"It was observed in {len(scenarios)} scenario(s)."
            )

            document = {

                "id": f'iot23_{attack.lower().replace(" ", "_").replace("&", "and")}',

                "source": "IoT23",

                "attack_type": attack,

                "summary":summary,

                "flow_count": int(flow_count),

                "protocol_distribution": protocol_distribution,

                "service_distribution": service_distribution,

                "connection_state_distribution": connection_state_distribution,

                "average_duration": float(
                 round(
                    avg_duration,
                    4
                 )
                ),

                "average_orig_bytes": float(
                round(
                    avg_orig_bytes,
                    2
                )
                ),

                "average_resp_bytes": float(
                round(
                    avg_resp_bytes,
                    2
                )
                ),

                "unique_source_ips": int(unique_source_ips),

                "unique_destination_ips": int(unique_destination_ips),

                "scenarios": scenarios

            }

            knowledge_documents.append(document)

        return knowledge_documents