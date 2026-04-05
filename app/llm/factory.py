from __future__ import annotations

import os

from app.llm.contracts import AnswerGenerator
from app.llm.providers.gemini import GeminiKbAnswerGenerator
from app.llm.providers.openai import OpenAIKbAnswerGenerator


class KbAnswerGeneratorFactory:
    def build(self) -> AnswerGenerator:
        provider = os.getenv("KB_ANSWER_PROVIDER", "openai").strip().lower()
        if provider == "openai":
            return OpenAIKbAnswerGenerator.from_env()
        if provider == "gemini":
            return GeminiKbAnswerGenerator.from_env()
        raise ValueError(
            "Unsupported KB_ANSWER_PROVIDER "
            f"'{provider}'. Use 'openai' or 'gemini'."
        )
