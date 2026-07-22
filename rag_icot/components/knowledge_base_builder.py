import json
import os


class KnowledgeBaseBuilder:

    def __init__(self):
        pass

    def save_documents(self, documents, output_path):

        # Create folder if it doesn't exist
        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        # Save JSON
        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                documents,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"Saved {len(documents)} documents to {output_path}"
        )
    def load_documents(self, file_path):

        with open(
        file_path,
        "r",
        encoding="utf-8"
        ) as f:

           documents = json.load(f)

        return documents

    def merge_documents(self, *document_lists):

        merged = []

        for docs in document_lists:

           merged.extend(docs)

        return merged    