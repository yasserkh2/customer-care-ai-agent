from __future__ import annotations

import os

from app.llm.contracts import IntentDecisionGenerator
from app.llm.providers.azure_openai import AzureOpenAIIntentDecisionGenerator
from app.llm.providers.gemini import GeminiIntentDecisionGenerator
from app.llm.providers.openai import OpenAIIntentDecisionGenerator


class IntentDecisionGeneratorFactory:
    def build(self) -> IntentDecisionGenerator:
        provider = os.getenv(
            "INTENT_CLASSIFIER_PROVIDER",
            os.getenv(
                "ACTION_AGENT_PROVIDER",
                os.getenv("KB_ANSWER_PROVIDER", "openai"),
            ),
        ).strip().lower()
        if provider == "openai":
            return OpenAIIntentDecisionGenerator.from_env()
        if provider == "azure_openai":
            return AzureOpenAIIntentDecisionGenerator.from_env()
        if provider == "gemini":
            return GeminiIntentDecisionGenerator.from_env()
        raise ValueError(
            "Unsupported INTENT_CLASSIFIER_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )
