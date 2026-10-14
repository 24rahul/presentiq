"""Create isolated provider clients without changing process configuration."""

import os

import openai

DEFAULT_OPENAI_MODEL = "gpt-5.5"


class AnalysisError(RuntimeError):
    """An evaluation failed; no performance score should be returned."""


class AIBackend:
    def __init__(self, provider="OpenAI", *, api_key=None, model=None):
        if provider not in ("OpenAI", "xAI (Grok)"):
            raise ValueError("Unsupported AI provider")
        self.provider = provider
        key_name = "OPENAI_API_KEY" if provider == "OpenAI" else "XAI_API_KEY"
        key = os.getenv(key_name, "") if api_key is None else api_key
        if not key.strip():
            raise ValueError(f"{provider} API access is not configured")
        if model:
            self.model = model
        elif provider == "OpenAI":
            self.model = os.getenv("AI_MODEL") or DEFAULT_OPENAI_MODEL
        else:
            self.model = os.getenv("GROK_MODEL") or "grok-3"
        self.temperature = float(os.getenv("FEEDBACK_TEMPERATURE", "0.3"))
        options = {"api_key": key, "timeout": 120.0, "max_retries": 1}
        if provider != "OpenAI":
            options["base_url"] = "https://api.x.ai/v1"
        self.client = openai.OpenAI(**options)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()
