from __future__ import annotations

import os

from app.llm.http import post_json
from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.prompts import DEFAULT_KB_SYSTEM_PROMPT, build_kb_user_prompt
from app.services.action_models import AppointmentActionReplyContext


class OpenAIKbAnswerGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_KB_SYSTEM_PROMPT,
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
    def from_env(cls) -> "OpenAIKbAnswerGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            system_prompt=os.getenv("KB_ANSWER_SYSTEM_PROMPT", DEFAULT_KB_SYSTEM_PROMPT),
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
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
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
