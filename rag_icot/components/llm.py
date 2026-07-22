import os

import google.generativeai as genai

from dotenv import load_dotenv


class GeminiLLM:

    def __init__(self):

        load_dotenv()

        api_key = os.getenv("GOOGLE_API_KEY")

        if api_key is None:
            raise ValueError(
                "GOOGLE_API_KEY not found in .env"
            )

        genai.configure(
            api_key=api_key
        )

        self.model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

    def generate(
        self,
        prompt
    ):

        response = self.model.generate_content(
            prompt
        )

        return response.text