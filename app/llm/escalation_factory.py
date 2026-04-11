from __future__ import annotations

import os

from app.llm.contracts import EscalationReplyGenerator
from app.llm.providers.azure_openai import AzureOpenAIEscalationReplyGenerator
from app.llm.providers.gemini import GeminiEscalationReplyGenerator
from app.llm.providers.openai import OpenAIEscalationReplyGenerator


class EscalationReplyGeneratorFactory:
    def build(self) -> EscalationReplyGenerator:
        provider = os.getenv(
            "ESCALATION_AGENT_PROVIDER",
            os.getenv(
                "ACTION_AGENT_PROVIDER",
                os.getenv("KB_ANSWER_PROVIDER", "openai"),
            ),
        ).strip().lower()
        if provider == "openai":
            return OpenAIEscalationReplyGenerator.from_env()
        if provider == "azure_openai":
            return AzureOpenAIEscalationReplyGenerator.from_env()
        if provider == "gemini":
            return GeminiEscalationReplyGenerator.from_env()
        raise ValueError(
            "Unsupported ESCALATION_AGENT_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )
