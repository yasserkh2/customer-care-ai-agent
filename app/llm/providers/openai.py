from __future__ import annotations

import os
import json
import re

from app.llm.http import post_json
from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.escalation_prompts import (
    DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT,
    build_escalation_user_prompt,
)
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
from app.services.action_models import AppointmentActionReplyContext
from app.services.models import IntentDecision


class OpenAIKbAnswerGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_KB_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
        max_output_tokens: int = 220,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI chat model must not be empty.")

        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max(1, int(max_output_tokens))

    @classmethod
    def from_env(cls) -> "OpenAIKbAnswerGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
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
        payload = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": self._max_output_tokens,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        response_payload = post_json(
            url=self._base_url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="OpenAI chat completions",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI chat response did not contain choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenAI chat response did not contain text content.")
        return content.strip()


class OpenAIActionReplyGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI chat model must not be empty.")

        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAIActionReplyGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
            system_prompt=os.getenv(
                "ACTION_AGENT_SYSTEM_PROMPT",
                DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
            ),
        )

    def generate_reply(self, context: AppointmentActionReplyContext) -> str:
        prompt = build_action_agent_user_prompt(context)
        payload = {
            "model": self._model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        response_payload = post_json(
            url=self._base_url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="OpenAI action reply generation",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI action reply did not contain choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenAI action reply did not contain text content.")
        return content.strip()


class OpenAIEscalationReplyGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
        max_output_tokens: int = 180,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI chat model must not be empty.")

        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max(1, int(max_output_tokens))

    @classmethod
    def from_env(cls) -> "OpenAIEscalationReplyGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
            system_prompt=os.getenv(
                "ESCALATION_AGENT_SYSTEM_PROMPT",
                DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT,
            ),
            max_output_tokens=int(
                os.getenv("ESCALATION_AGENT_MAX_OUTPUT_TOKENS", "180")
            ),
        )

    def generate_reply(
        self,
        *,
        user_query: str,
        escalation_reason: str,
        conversation_history: list[str],
        escalation_case_id: str | None,
        contact_name: str | None,
        contact_email: str | None,
        contact_phone: str | None,
        requires_contact: bool,
    ) -> str:
        prompt = build_escalation_user_prompt(
            user_query=user_query,
            escalation_reason=escalation_reason,
            conversation_history=conversation_history,
            escalation_case_id=escalation_case_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            requires_contact=requires_contact,
        )
        payload = {
            "model": self._model,
            "temperature": 0.3,
            "max_tokens": self._max_output_tokens,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        response_payload = post_json(
            url=self._base_url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="OpenAI escalation reply generation",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI escalation reply did not contain choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenAI escalation reply did not contain text content.")
        return content.strip()


class OpenAIIntentDecisionGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI chat model must not be empty.")

        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAIIntentDecisionGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
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
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        response_payload = post_json(
            url=self._base_url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="OpenAI intent classification",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI intent classification did not contain choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "OpenAI intent classification did not contain text content."
            )
        return _parse_intent_decision_text(content)


class OpenAIRetrievalQueryGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI chat model must not be empty.")

        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAIRetrievalQueryGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv(
                "OPENAI_RETRIEVAL_QUERY_MODEL",
                os.getenv(
                    "RETRIEVAL_QUERY_MODEL",
                    os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
                ),
            ),
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
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        response_payload = post_json(
            url=self._base_url,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="OpenAI retrieval query generation",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI retrieval query response did not contain choices.")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "OpenAI retrieval query response did not contain text content."
            )
        return content.strip()


def _parse_intent_decision_text(content: str) -> IntentDecision:
    json_block_match = re.search(r"\{.*\}", content, re.DOTALL)
    raw_json = json_block_match.group(0) if json_block_match else content
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise RuntimeError("Intent classification payload was not a JSON object.")
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
