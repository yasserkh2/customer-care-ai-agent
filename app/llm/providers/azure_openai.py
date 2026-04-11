from __future__ import annotations

import os
from urllib import parse

from app.llm.action_extraction import (
    DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
    build_action_extraction_prompt,
)
from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.http import post_json
from app.llm.intent_prompts import (
    DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
    build_intent_classifier_prompt,
    parse_intent_decision_payload,
)
from app.llm.prompts import DEFAULT_KB_SYSTEM_PROMPT, build_kb_user_prompt
from app.llm.retrieval_query_prompts import (
    DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
    build_retrieval_query_prompt,
)
from app.services.action_models import AppointmentActionReplyContext, AppointmentExtraction
from app.services.models import IntentDecision


class AzureOpenAIKbAnswerGenerator:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_KB_SYSTEM_PROMPT,
        timeout_seconds: int = 60,
        max_output_tokens: int = 220,
    ) -> None:
        self._api_key = _require_non_empty(api_key, "AZURE_OPENAI_API_KEY")
        self._endpoint = _normalize_endpoint(
            _require_non_empty(endpoint, "AZURE_OPENAI_ENDPOINT")
        )
        self._deployment = _require_non_empty(
            deployment,
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        self._api_version = _require_non_empty(
            api_version,
            "AZURE_OPENAI_API_VERSION",
        )
        self._system_prompt = system_prompt
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max(1, int(max_output_tokens))

    @classmethod
    def from_env(cls) -> "AzureOpenAIKbAnswerGenerator":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv("KB_ANSWER_SYSTEM_PROMPT", DEFAULT_KB_SYSTEM_PROMPT),
            max_output_tokens=int(os.getenv("KB_ANSWER_MAX_OUTPUT_TOKENS", "220")),
        )

    def generate_answer(
        self,
        user_query: str,
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        prompt = build_kb_user_prompt(
            user_query=user_query,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history,
        )
        response_payload = post_json(
            url=_build_chat_completions_url(
                endpoint=self._endpoint,
                deployment=self._deployment,
                api_version=self._api_version,
            ),
            payload={
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": self._max_output_tokens,
            },
            headers=_azure_headers(self._api_key),
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI chat completions",
        )
        return _parse_chat_completion_text(
            response_payload,
            error_prefix="Azure OpenAI chat response",
        )


class AzureOpenAIActionReplyGenerator:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = _require_non_empty(api_key, "AZURE_OPENAI_API_KEY")
        self._endpoint = _normalize_endpoint(
            _require_non_empty(endpoint, "AZURE_OPENAI_ENDPOINT")
        )
        self._deployment = _require_non_empty(
            deployment,
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        self._api_version = _require_non_empty(
            api_version,
            "AZURE_OPENAI_API_VERSION",
        )
        self._system_prompt = system_prompt
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "AzureOpenAIActionReplyGenerator":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv(
                "ACTION_AGENT_SYSTEM_PROMPT",
                DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
            ),
        )

    def generate_reply(self, context: AppointmentActionReplyContext) -> str:
        prompt = build_action_agent_user_prompt(context)
        response_payload = post_json(
            url=_build_chat_completions_url(
                endpoint=self._endpoint,
                deployment=self._deployment,
                api_version=self._api_version,
            ),
            payload={
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
            headers=_azure_headers(self._api_key),
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI action reply generation",
        )
        return _parse_chat_completion_text(
            response_payload,
            error_prefix="Azure OpenAI action reply",
        )


class AzureOpenAIAppointmentExtractor:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = _require_non_empty(api_key, "AZURE_OPENAI_API_KEY")
        self._endpoint = _normalize_endpoint(
            _require_non_empty(endpoint, "AZURE_OPENAI_ENDPOINT")
        )
        self._deployment = _require_non_empty(
            deployment,
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        self._api_version = _require_non_empty(
            api_version,
            "AZURE_OPENAI_API_VERSION",
        )
        self._system_prompt = system_prompt
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "AzureOpenAIAppointmentExtractor":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv(
                "ACTION_EXTRACTION_SYSTEM_PROMPT",
                DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
            ),
        )

    def extract(
        self,
        user_query: str,
        conversation_history: list[str],
        current_slots: dict[str, str],
        offered_dates: list[str] | None = None,
        offered_times: list[str] | None = None,
        offered_services: list[str] | None = None,
        awaiting_confirmation: bool = False,
    ) -> AppointmentExtraction:
        prompt = build_action_extraction_prompt(
            user_query=user_query,
            conversation_history=conversation_history,
            current_slots=current_slots,
            offered_dates=offered_dates,
            offered_times=offered_times,
            offered_services=offered_services,
            awaiting_confirmation=awaiting_confirmation,
        )
        response_payload = post_json(
            url=_build_chat_completions_url(
                endpoint=self._endpoint,
                deployment=self._deployment,
                api_version=self._api_version,
            ),
            payload={
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            },
            headers=_azure_headers(self._api_key),
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI appointment extraction",
        )
        content = _parse_chat_completion_text(
            response_payload,
            error_prefix="Azure OpenAI extraction response",
        )
        return AppointmentExtraction(
            service=_extract_string_field(content, "service"),
            date=_extract_string_field(content, "date"),
            time=_extract_string_field(content, "time"),
            time_preference=_extract_string_field(content, "time_preference"),
            selected_date=_extract_string_field(content, "selected_date"),
            selected_time=_extract_string_field(content, "selected_time"),
            selected_service=_extract_string_field(content, "selected_service"),
            confirmation_intent=_extract_string_field(content, "confirmation_intent"),
            name=_extract_string_field(content, "name"),
            email=_extract_string_field(content, "email"),
        )


class AzureOpenAIIntentDecisionGenerator:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = _require_non_empty(api_key, "AZURE_OPENAI_API_KEY")
        self._endpoint = _normalize_endpoint(
            _require_non_empty(endpoint, "AZURE_OPENAI_ENDPOINT")
        )
        self._deployment = _require_non_empty(
            deployment,
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        self._api_version = _require_non_empty(
            api_version,
            "AZURE_OPENAI_API_VERSION",
        )
        self._system_prompt = system_prompt
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "AzureOpenAIIntentDecisionGenerator":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv(
                "INTENT_CLASSIFIER_SYSTEM_PROMPT",
                DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
            ),
        )

    def classify_intent(
        self,
        user_query: str,
        conversation_history: list[str],
        active_action: str | None,
        failure_count: int,
    ) -> IntentDecision:
        prompt = build_intent_classifier_prompt(
            user_query=user_query,
            conversation_history=conversation_history,
            active_action=active_action,
            failure_count=failure_count,
        )
        response_payload = post_json(
            url=_build_chat_completions_url(
                endpoint=self._endpoint,
                deployment=self._deployment,
                api_version=self._api_version,
            ),
            payload={
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            },
            headers=_azure_headers(self._api_key),
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI intent classification",
        )
        content = _parse_chat_completion_text(
            response_payload,
            error_prefix="Azure OpenAI intent classification",
        )
        payload = _extract_json_payload(content)
        parsed = parse_intent_decision_payload(payload)
        return IntentDecision(
            intent=parsed["intent"],
            confidence=parsed["confidence"],
            frustration_flag=parsed["frustration_flag"],
            escalation_reason=parsed["escalation_reason"],
            escalation_contact_name=parsed["escalation_contact_name"],
            escalation_contact_email=parsed["escalation_contact_email"],
            escalation_contact_phone=parsed["escalation_contact_phone"],
        )


class AzureOpenAIRetrievalQueryGenerator:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = _require_non_empty(api_key, "AZURE_OPENAI_API_KEY")
        self._endpoint = _normalize_endpoint(
            _require_non_empty(endpoint, "AZURE_OPENAI_ENDPOINT")
        )
        self._deployment = _require_non_empty(
            deployment,
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        self._api_version = _require_non_empty(
            api_version,
            "AZURE_OPENAI_API_VERSION",
        )
        self._system_prompt = system_prompt
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "AzureOpenAIRetrievalQueryGenerator":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_RETRIEVAL_QUERY_DEPLOYMENT",
                os.getenv(
                    "AZURE_OPENAI_CHAT_DEPLOYMENT",
                    os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
                ),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv(
                "RETRIEVAL_QUERY_SYSTEM_PROMPT",
                DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
            ),
        )

    def generate_query(
        self,
        user_query: str,
        conversation_history: list[str],
    ) -> str:
        prompt = build_retrieval_query_prompt(
            user_query=user_query,
            conversation_history=conversation_history,
        )
        response_payload = post_json(
            url=_build_chat_completions_url(
                endpoint=self._endpoint,
                deployment=self._deployment,
                api_version=self._api_version,
            ),
            payload={
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            },
            headers=_azure_headers(self._api_key),
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI retrieval query generation",
        )
        return _parse_chat_completion_text(
            response_payload,
            error_prefix="Azure OpenAI retrieval query generation",
        )


def _build_chat_completions_url(
    endpoint: str,
    deployment: str,
    api_version: str,
) -> str:
    quoted_deployment = parse.quote(deployment, safe="")
    query = parse.urlencode({"api-version": api_version})
    return (
        f"{endpoint}/openai/deployments/{quoted_deployment}/chat/completions?{query}"
    )


def _azure_headers(api_key: str) -> dict[str, str]:
    return {
        "api-key": api_key,
        "Content-Type": "application/json",
    }


def _parse_chat_completion_text(
    response_payload: dict[str, object],
    error_prefix: str,
) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"{error_prefix} did not contain choices.")

    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"{error_prefix} did not contain text content.")
    return content.strip()


def _extract_string_field(content: str, field_name: str) -> str | None:
    import json
    import re

    json_block_match = re.search(r"\{.*\}", content, re.DOTALL)
    raw_json = json_block_match.group(0) if json_block_match else content
    payload = json.loads(raw_json)
    value = payload.get(field_name) if isinstance(payload, dict) else None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _extract_json_payload(content: str) -> dict[str, object]:
    import json
    import re

    json_block_match = re.search(r"\{.*\}", content, re.DOTALL)
    raw_json = json_block_match.group(0) if json_block_match else content
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise RuntimeError("Intent classification payload was not a JSON object.")
    return payload


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip().rstrip("/")


def _require_non_empty(value: str, env_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{env_name} must not be empty.")
    return normalized
