from __future__ import annotations

import json
import os
import re
from datetime import date
from urllib import parse

from app.llm.http import post_json
from app.services.action_models import AppointmentExtraction

DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT = (
    "You extract appointment-booking details from customer messages. "
    "Return JSON only. "
    "Do not invent missing details. "
    "Use null for unknown values. "
    "Understand relative dates such as today, tomorrow, next Monday, and this afternoon. "
    "Set time only when the user gives a specific time. "
    "Use time_preference for broad phrases like morning, afternoon, or evening. "
    "When service options are provided, map partial or informal service mentions to the exact offered service name in selected_service. "
    "When dates or times are offered, map the user's selection to the exact offered option in selected_date or selected_time. "
    "When a user confirms or wants changes, set confirmation_intent to confirm or change. "
    "If awaiting_confirmation is true and the latest user message expresses agreement, approval, or readiness to proceed, set confirmation_intent to confirm. "
    "If awaiting_confirmation is true and the latest user message rejects the proposal or asks to modify a detail, set confirmation_intent to change."
)


def build_action_extraction_prompt(
    user_query: str,
    conversation_history: list[str],
    current_slots: dict[str, str],
    offered_dates: list[str] | None = None,
    offered_times: list[str] | None = None,
    offered_services: list[str] | None = None,
    awaiting_confirmation: bool = False,
) -> str:
    history_block = "\n".join(conversation_history[-6:]) or "[no prior conversation]"
    current_slots_json = json.dumps(current_slots, sort_keys=True)
    offered_dates_json = json.dumps(offered_dates or [])
    offered_times_json = json.dumps(offered_times or [])
    offered_services_json = json.dumps(offered_services or [])
    today_iso = date.today().isoformat()
    return (
        "Extract appointment booking fields from the conversation.\n\n"
        f"Today's date:\n{today_iso}\n\n"
        f"Recent conversation:\n{history_block}\n\n"
        f"Current known slots:\n{current_slots_json}\n\n"
        f"Currently offered dates:\n{offered_dates_json}\n\n"
        f"Currently offered times:\n{offered_times_json}\n\n"
        f"Currently offered services:\n{offered_services_json}\n\n"
        f"Awaiting confirmation:\n{json.dumps(awaiting_confirmation)}\n\n"
        f"Latest user message:\n{user_query}\n\n"
        "If the user is choosing from offered dates, times, or services, return the exact offered option in selected_date, selected_time, or selected_service.\n"
        "Prefer selected_service over service whenever a service option can be matched exactly.\n"
        "Prefer selected_date or selected_time over raw date or time whenever the user is picking from offered options.\n"
        "Interpret relative dates using today's date only when needed to understand the intent.\n"
        "If awaiting_confirmation is true, map messages such as yes, sure, confirmed, go ahead, book it, or proceed to confirmation_intent=\"confirm\".\n"
        "If awaiting_confirmation is true, map messages such as no, change it, different time, or update the date to confirmation_intent=\"change\".\n"
        "Return valid JSON with exactly these keys:\n"
        '{"service": null, "date": null, "time": null, "time_preference": null, "selected_date": null, "selected_time": null, "selected_service": null, "confirmation_intent": null, "name": null, "email": null}'
    )


class AppointmentExtractorFactory:
    def build(self) -> "LlmAppointmentExtractor":
        provider = os.getenv(
            "ACTION_EXTRACTION_PROVIDER",
            os.getenv("KB_ANSWER_PROVIDER", "gemini"),
        ).strip().lower()
        if provider == "openai":
            return OpenAIAppointmentExtractor.from_env()
        if provider == "azure_openai":
            from app.llm.providers.azure_openai import AzureOpenAIAppointmentExtractor

            return AzureOpenAIAppointmentExtractor.from_env()
        if provider == "gemini":
            return GeminiAppointmentExtractor.from_env()
        raise ValueError(
            "Unsupported ACTION_EXTRACTION_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )


class LlmAppointmentExtractor:
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
        raise NotImplementedError


class OpenAIAppointmentExtractor(LlmAppointmentExtractor):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAIAppointmentExtractor":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
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
            provider_name="OpenAI appointment extraction",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI extraction response did not contain choices.")
        content = choices[0].get("message", {}).get("content", "")
        return _parse_extraction_content(str(content))


class GeminiAppointmentExtractor(LlmAppointmentExtractor):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_EXTRACTION_SYSTEM_PROMPT,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = api_key
        self._model = self._normalize_model_name(model)
        self._system_prompt = system_prompt
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "GeminiAppointmentExtractor":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
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
            provider_name="Gemini appointment extraction",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini extraction response did not contain candidates.")
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "\n".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
        return _parse_extraction_content(text)

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"


def _parse_extraction_content(content: str) -> AppointmentExtraction:
    json_block_match = re.search(r"\{.*\}", content, re.DOTALL)
    raw_json = json_block_match.group(0) if json_block_match else content
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise RuntimeError("Appointment extraction payload was not a JSON object.")
    return AppointmentExtraction(
        service=_string_or_none(payload.get("service")),
        date=_string_or_none(payload.get("date")),
        time=_string_or_none(payload.get("time")),
        time_preference=_string_or_none(payload.get("time_preference")),
        selected_date=_string_or_none(payload.get("selected_date")),
        selected_time=_string_or_none(payload.get("selected_time")),
        selected_service=_string_or_none(payload.get("selected_service")),
        confirmation_intent=_string_or_none(payload.get("confirmation_intent")),
        name=_string_or_none(payload.get("name")),
        email=_string_or_none(payload.get("email")),
    )


def _string_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
