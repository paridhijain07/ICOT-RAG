import os
import pandas as pd


class DataIngestion:

    def load_iot23(self, file_path):

        # Extract Columns
        columns = None

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#fields"):

                    fields = line.strip().split("\t")[1:]

                    last_field = fields.pop()

                    last_parts = last_field.split()

                    fields.extend(last_parts)

                    columns = fields

                    break

        # Extract Rows
        rows = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:

                if not line.startswith("#"):

                    parts = line.strip().split("\t")

                    last_field = parts.pop()

                    last_parts = last_field.split()

                    parts.extend(last_parts)

                    rows.append(parts)

        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)

        return df


    def load_all_iot23(self, dataset_folder):

        all_data = []

        for folder in os.listdir(dataset_folder):

            scenario_path = os.path.join(
                dataset_folder,
                folder,
                "bro",
                "conn.log.labeled"
            )

            if os.path.exists(scenario_path):

                print(f"Loading {folder}")

                df = self.load_iot23(scenario_path)

                df["scenario"] = folder

                all_data.append(df)

        combined_df = pd.concat(
            all_data,
            ignore_index=True
        )

        return combined_df