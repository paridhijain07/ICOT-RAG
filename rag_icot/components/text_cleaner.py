import re


class TextCleaner:

    def __init__(self):
        pass

    def extract_field(self, value):
        """Normalize VARIoT nested fields like {'data': '...'} to plain text."""

        if value is None:
            return ""

        if isinstance(value, dict):
            if "data" in value:
                return self.extract_field(value.get("data"))
            return ""

        if isinstance(value, list):
            parts = [
                self.extract_field(item)
                for item in value
            ]
            return ", ".join(
                part for part in parts if part
            )

        return str(value)

    def clean(self, text, max_length=None):

        text = self.extract_field(text)

        # Remove HTML tags
        text = re.sub(r"<.*?>", " ", text)

        # Replace newlines and tabs
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")

        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)

        text = text.strip()

        if max_length is not None and len(text) > max_length:
            text = text[:max_length].rstrip() + "..."

        return text
