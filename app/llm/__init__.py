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
from app.llm.contracts import ActionReplyGenerator, AnswerGenerator, IntentDecisionGenerator
from app.llm.factory import KbAnswerGeneratorFactory
from app.llm.intent_factory import IntentDecisionGeneratorFactory
from app.llm.intent_prompts import (
    DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
    build_intent_classifier_prompt,
)
from app.llm.providers import (
    AzureOpenAIActionReplyGenerator,
    AzureOpenAIAppointmentExtractor,
    AzureOpenAIIntentDecisionGenerator,
    AzureOpenAIKbAnswerGenerator,
)
from app.llm.prompts import (
    DEFAULT_KB_SYSTEM_PROMPT,
    build_kb_user_prompt,
)
from app.llm.retrieval_query_factory import RetrievalQueryGeneratorFactory
from app.llm.retrieval_query_prompts import (
    DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
    build_retrieval_query_prompt,
)

__all__ = [
    "AnswerGenerator",
    "ActionReplyGenerator",
    "IntentDecisionGenerator",
    "ActionReplyGeneratorFactory",
    "AppointmentExtractorFactory",
    "AzureOpenAIActionReplyGenerator",
    "AzureOpenAIAppointmentExtractor",
    "AzureOpenAIIntentDecisionGenerator",
    "AzureOpenAIKbAnswerGenerator",
    "DEFAULT_ACTION_AGENT_SYSTEM_PROMPT",
    "DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT",
    "KbAnswerGeneratorFactory",
    "IntentDecisionGeneratorFactory",
    "RetrievalQueryGeneratorFactory",
    "build_action_agent_user_prompt",
    "build_action_extraction_prompt",
    "DEFAULT_KB_SYSTEM_PROMPT",
    "DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT",
    "build_kb_user_prompt",
    "build_intent_classifier_prompt",
    "DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT",
    "build_retrieval_query_prompt",
]
