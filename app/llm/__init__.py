"""LLM package for prompt construction and provider-backed text generation."""

from app.llm.contracts import AnswerGenerator
from app.llm.factory import KbAnswerGeneratorFactory
from app.llm.prompts import (
    DEFAULT_KB_SYSTEM_PROMPT,
    build_kb_user_prompt,
    is_conversational_query,
)

__all__ = [
    "AnswerGenerator",
    "KbAnswerGeneratorFactory",
    "DEFAULT_KB_SYSTEM_PROMPT",
    "build_kb_user_prompt",
    "is_conversational_query",
]
