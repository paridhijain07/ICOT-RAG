import os
import time
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """Load .env from project root even when cwd is notebooks/."""

    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    # override=True so notebook kernels pick up provider switches
    load_dotenv(dotenv_path=env_path, override=True)


_load_env()


class GeminiBackend:
    """Google Gemini backend."""

    def __init__(
        self,
        model_name=None,
        max_retries=5,
        base_delay_seconds=20,
    ):
        import google.generativeai as genai
        from google.api_core import exceptions as google_exceptions

        self._google_exceptions = google_exceptions

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env")

        genai.configure(api_key=api_key)

        self.model_name = model_name or os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )
        self.model = genai.GenerativeModel(self.model_name)
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.provider = "gemini"

    def generate(self, prompt: str) -> str:
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text

            except self._google_exceptions.ResourceExhausted as exc:
                last_error = exc
                delay = self.base_delay_seconds * (attempt + 1)
                print(
                    f"Gemini quota/rate limit hit. "
                    f"Retry {attempt + 1}/{self.max_retries} in {delay}s..."
                )
                time.sleep(delay)

            except self._google_exceptions.GoogleAPIError as exc:
                last_error = exc
                if attempt >= self.max_retries - 1:
                    raise
                delay = self.base_delay_seconds
                print(
                    f"Gemini API error ({type(exc).__name__}). "
                    f"Retry {attempt + 1}/{self.max_retries} in {delay}s..."
                )
                time.sleep(delay)

        raise last_error


class GroqBackend:
    """Groq OpenAI-compatible chat backend."""

    def __init__(
        self,
        model_name=None,
        max_retries=5,
        base_delay_seconds=5,
    ):
        from groq import Groq
        from groq import RateLimitError, APIStatusError

        self._RateLimitError = RateLimitError
        self._APIStatusError = APIStatusError

        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if not api_key:
            env_file = Path(__file__).resolve().parents[2] / ".env"
            raise ValueError(
                f"GROQ_API_KEY is missing or empty in {env_file} "
                "(save the file after pasting). Get a key at "
                "https://console.groq.com/keys"
            )

        self.model_name = model_name or os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )
        self.client = Groq(api_key=api_key)
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.provider = "groq"

    def generate(self, prompt: str) -> str:
        last_error = None
        # gpt-oss models on Groq may try built-in tools (browser.search) unless
        # we force text-only + tool_choice=none.
        system = (
            "You are a text-only assistant. Never call tools, functions, or "
            "browsers. Never emit tool-call JSON. Reply with plain text or the "
            "exact JSON the user requested."
        )

        for attempt in range(self.max_retries):
            try:
                user_content = prompt
                if attempt > 0:
                    user_content = (
                        "IMPORTANT: Do not call any tools. Answer directly.\n\n"
                        + prompt
                    )
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.2,
                    tool_choice="none",
                )
                content = response.choices[0].message.content
                return content if content is not None else ""

            except self._RateLimitError as exc:
                last_error = exc
                delay = self.base_delay_seconds * (attempt + 1)
                print(
                    f"Groq rate limit hit. "
                    f"Retry {attempt + 1}/{self.max_retries} in {delay}s..."
                )
                time.sleep(delay)

            except self._APIStatusError as exc:
                last_error = exc
                msg = str(exc).lower()
                # Model tried a built-in tool despite tool_choice=none — retry.
                if getattr(exc, "status_code", None) == 400 and (
                    "tool" in msg or "tool_use_failed" in msg
                ):
                    print(
                        f"Groq tool-call refused (attempt "
                        f"{attempt + 1}/{self.max_retries}); retrying text-only..."
                    )
                    time.sleep(1)
                    continue
                if attempt >= self.max_retries - 1:
                    raise
                delay = self.base_delay_seconds
                print(
                    f"Groq API error ({exc.status_code}). "
                    f"Retry {attempt + 1}/{self.max_retries} in {delay}s..."
                )
                time.sleep(delay)

        raise last_error


def create_llm(
    provider=None,
    model_name=None,
    max_retries=5,
    base_delay_seconds=None,
):
    """Create an LLM backend from env or explicit provider."""

    # Reload every time so notebooks pick up .env edits without kernel restart
    _load_env()

    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).strip().lower()

    if provider == "groq":
        return GroqBackend(
            model_name=model_name,
            max_retries=max_retries,
            base_delay_seconds=(
                5 if base_delay_seconds is None else base_delay_seconds
            ),
        )

    if provider in {"gemini", "google"}:
        return GeminiBackend(
            model_name=model_name,
            max_retries=max_retries,
            base_delay_seconds=(
                20 if base_delay_seconds is None else base_delay_seconds
            ),
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER='{provider}'. Use 'groq' or 'gemini'."
    )


class GeminiLLM:
    """Backward-compatible LLM entry point used across the project.

    Provider is selected by LLM_PROVIDER in .env:
      - groq   (default)
      - gemini
    """

    def __init__(
        self,
        model_name=None,
        max_retries=5,
        base_delay_seconds=None,
        provider=None,
    ):
        self._backend = create_llm(
            provider=provider,
            model_name=model_name,
            max_retries=max_retries,
            base_delay_seconds=base_delay_seconds,
        )
        self.provider = self._backend.provider
        self.model_name = getattr(
            self._backend,
            "model_name",
            None,
        )
        print(
            f"LLM ready: provider={self.provider}, "
            f"model={self.model_name}"
        )

    def generate(self, prompt: str) -> str:
        return self._backend.generate(prompt)
