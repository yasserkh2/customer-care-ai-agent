from __future__ import annotations

import os
from urllib import parse

from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.http import post_json
from app.llm.prompts import DEFAULT_KB_SYSTEM_PROMPT, build_kb_user_prompt
from app.services.action_models import AppointmentActionReplyContext


class GeminiKbAnswerGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_KB_SYSTEM_PROMPT,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("Gemini model must not be empty.")

        self._api_key = api_key
        self._model = self._normalize_model_name(model)
        self._system_prompt = system_prompt
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "GeminiKbAnswerGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        response_payload = post_json(
            url=endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Gemini generateContent",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini response did not contain candidates.")

        content = candidates[0].get("content", {})
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise RuntimeError("Gemini response did not contain content parts.")

        text_parts = [
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        answer = "\n".join(part for part in text_parts if part).strip()
        if not answer:
            raise RuntimeError("Gemini response did not contain text content.")
        return answer

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"


class GeminiActionReplyGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY must not be empty.")
        if not model.strip():
            raise ValueError("Gemini model must not be empty.")

        self._api_key = api_key
        self._model = self._normalize_model_name(model)
        self._system_prompt = system_prompt
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "GeminiActionReplyGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
            system_prompt=os.getenv(
                "ACTION_AGENT_SYSTEM_PROMPT",
                DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
            ),
        )

    def generate_reply(self, context: AppointmentActionReplyContext) -> str:
        prompt = build_action_agent_user_prompt(context)
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }
        response_payload = post_json(
            url=endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Gemini action reply generation",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini action reply did not contain candidates.")

        content = candidates[0].get("content", {})
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise RuntimeError("Gemini action reply did not contain content parts.")

        text_parts = [
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        answer = "\n".join(part for part in text_parts if part).strip()
        if not answer:
            raise RuntimeError("Gemini action reply did not contain text content.")
        return answer

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"
