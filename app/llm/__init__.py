"""LLM package for prompt construction and provider-backed text generation."""

from app.llm.action_extraction import (
    AppointmentExtractorFactory,
    DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
    build_action_extraction_prompt,
)
from app.llm.action_factory import ActionReplyGeneratorFactory
from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.contracts import ActionReplyGenerator, AnswerGenerator
from app.llm.factory import KbAnswerGeneratorFactory
from app.llm.providers import (
    AzureOpenAIActionReplyGenerator,
    AzureOpenAIAppointmentExtractor,
    AzureOpenAIKbAnswerGenerator,
)
from app.llm.prompts import (
    DEFAULT_KB_SYSTEM_PROMPT,
    build_kb_user_prompt,
    is_conversational_query,
)

__all__ = [
    "AnswerGenerator",
    "ActionReplyGenerator",
    "ActionReplyGeneratorFactory",
    "AppointmentExtractorFactory",
    "AzureOpenAIActionReplyGenerator",
    "AzureOpenAIAppointmentExtractor",
    "AzureOpenAIKbAnswerGenerator",
    "DEFAULT_ACTION_AGENT_SYSTEM_PROMPT",
    "DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT",
    "KbAnswerGeneratorFactory",
    "build_action_agent_user_prompt",
    "build_action_extraction_prompt",
    "DEFAULT_KB_SYSTEM_PROMPT",
    "build_kb_user_prompt",
    "is_conversational_query",
]
