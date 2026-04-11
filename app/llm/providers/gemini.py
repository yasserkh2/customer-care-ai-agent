from __future__ import annotations

import os
import json
import re
from urllib import parse

from app.llm.action_prompts import (
    DEFAULT_ACTION_AGENT_SYSTEM_PROMPT,
    build_action_agent_user_prompt,
)
from app.llm.escalation_prompts import (
    DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT,
    build_escalation_user_prompt,
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
from app.services.action_models import AppointmentActionReplyContext
from app.services.models import IntentDecision


class GeminiKbAnswerGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_KB_SYSTEM_PROMPT,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
        max_output_tokens: int = 220,
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
        self._max_output_tokens = max(1, int(max_output_tokens))

    @classmethod
    def from_env(cls) -> "GeminiKbAnswerGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": self._max_output_tokens,
            },
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


class GeminiEscalationReplyGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
        max_output_tokens: int = 180,
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
        self._max_output_tokens = max(1, int(max_output_tokens))

    @classmethod
    def from_env(cls) -> "GeminiEscalationReplyGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": self._max_output_tokens,
            },
        }
        response_payload = post_json(
            url=endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Gemini escalation reply generation",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini escalation reply did not contain candidates.")

        content = candidates[0].get("content", {})
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise RuntimeError("Gemini escalation reply did not contain content parts.")

        text_parts = [
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        answer = "\n".join(part for part in text_parts if part).strip()
        if not answer:
            raise RuntimeError("Gemini escalation reply did not contain text content.")
        return answer

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"


class GeminiIntentDecisionGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT,
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
    def from_env(cls) -> "GeminiIntentDecisionGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        response_payload = post_json(
            url=endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Gemini intent classification",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini intent classification did not contain candidates.")

        content = candidates[0].get("content", {})
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise RuntimeError(
                "Gemini intent classification did not contain content parts."
            )

        text = "\n".join(
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ).strip()
        if not text:
            raise RuntimeError("Gemini intent classification did not contain text content.")
        return _parse_intent_decision_text(text)

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"


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


class GeminiRetrievalQueryGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_RETRIEVAL_QUERY_SYSTEM_PROMPT,
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
    def from_env(cls) -> "GeminiRetrievalQueryGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv(
                "GEMINI_RETRIEVAL_QUERY_MODEL",
                os.getenv(
                    "RETRIEVAL_QUERY_MODEL",
                    os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
        endpoint = (
            f"{self._base_url}/{self._model}:generateContent"
            f"?{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        response_payload = post_json(
            url=endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Gemini retrieval query generation",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError(
                "Gemini retrieval query generation did not contain candidates."
            )

        content = candidates[0].get("content", {})
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise RuntimeError(
                "Gemini retrieval query generation did not contain content parts."
            )

        text = "\n".join(
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ).strip()
        if not text:
            raise RuntimeError(
                "Gemini retrieval query generation did not contain text content."
            )
        return text

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"
