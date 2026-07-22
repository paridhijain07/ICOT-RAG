import re


class TextCleaner:

    def __init__(self):
        pass

    def clean(self, text):

        if text is None:
            return ""

        text = str(text)

        # Remove HTML tags
        text = re.sub(r"<.*?>", " ", text)

        # Replace newlines and tabs
        text = text.replace("\n", " ")
        text = text.replace("\t", " ")

        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text.strip()