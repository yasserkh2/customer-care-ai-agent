from __future__ import annotations

import os

from app.llm.contracts import ActionReplyGenerator
from app.llm.providers.azure_openai import AzureOpenAIActionReplyGenerator
from app.llm.providers.gemini import GeminiActionReplyGenerator
from app.llm.providers.openai import OpenAIActionReplyGenerator


class ActionReplyGeneratorFactory:
    def build(self) -> ActionReplyGenerator:
        provider = os.getenv(
            "ACTION_AGENT_PROVIDER",
            os.getenv("KB_ANSWER_PROVIDER", "openai"),
        ).strip().lower()
        if provider == "openai":
            return OpenAIActionReplyGenerator.from_env()
        if provider == "azure_openai":
            return AzureOpenAIActionReplyGenerator.from_env()
        if provider == "gemini":
            return GeminiActionReplyGenerator.from_env()
        raise ValueError(
            "Unsupported ACTION_AGENT_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )
