from __future__ import annotations

import os

from app.llm.contracts import RetrievalQueryGenerator
from app.llm.providers.azure_openai import AzureOpenAIRetrievalQueryGenerator
from app.llm.providers.gemini import GeminiRetrievalQueryGenerator
from app.llm.providers.openai import OpenAIRetrievalQueryGenerator


class RetrievalQueryGeneratorFactory:
    def build(self) -> RetrievalQueryGenerator:
        provider = os.getenv(
            "RETRIEVAL_QUERY_PROVIDER",
            os.getenv("KB_ANSWER_PROVIDER", "openai"),
        ).strip().lower()
        if provider == "openai":
            return OpenAIRetrievalQueryGenerator.from_env()
        if provider == "azure_openai":
            return AzureOpenAIRetrievalQueryGenerator.from_env()
        if provider == "gemini":
            return GeminiRetrievalQueryGenerator.from_env()
        raise ValueError(
            "Unsupported RETRIEVAL_QUERY_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )
