from __future__ import annotations

import json
import os
import re
from urllib import parse

from app.llm.http import post_json
from app.services.action_models import (
    AppointmentActionDecision,
    AppointmentActionPlanningContext,
)

DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT = (
    "You are the appointment scheduling planner for COB Company. "
    "You decide the next action for the agent. "
    "Return JSON only. "
    "Use the provided state and conversation to decide what to do next. "
    "Own the policy for slot collection, offered-option selection, confirmation, and when to call external availability or booking operations. "
    "When offered services, dates, or times are provided, map the user to the exact offered option in slot_updates. "
    "Do not invent booking results or unavailable options. "
    "Use clear_slots to remove stale values when the user changes their mind or when a tentative date or time must be reselected."
)


def build_action_planning_prompt(context: AppointmentActionPlanningContext) -> str:
    history_block = "\n".join(context.conversation_history[-8:]) or "[no prior conversation]"
    current_slots_json = json.dumps(context.current_slots, sort_keys=True)
    missing_fields_json = json.dumps(context.missing_fields)
    service_options_json = json.dumps(context.service_options)
    available_dates_json = json.dumps(context.available_dates)
    available_slots_json = json.dumps(context.available_slots)
    return (
        "Plan the next action for the appointment agent.\n\n"
        f"Latest user message:\n{context.user_query}\n\n"
        f"Recent conversation:\n{history_block}\n\n"
        f"Current slots:\n{current_slots_json}\n\n"
        f"Missing fields:\n{missing_fields_json}\n\n"
        f"Service options:\n{service_options_json}\n\n"
        f"Available dates:\n{available_dates_json}\n\n"
        f"Available times:\n{available_slots_json}\n\n"
        f"Date confirmed: {json.dumps(context.date_confirmed)}\n"
        f"Time confirmed: {json.dumps(context.time_confirmed)}\n"
        f"Awaiting confirmation: {json.dumps(context.awaiting_confirmation)}\n"
        f"Suggested date awaiting validation: {json.dumps(context.suggested_date)}\n"
        f"Suggested time awaiting validation: {json.dumps(context.suggested_time)}\n\n"
        "Return valid JSON with exactly these keys:\n"
        '{"phase": "collecting", "operation": null, "slot_updates": {}, "clear_slots": [], "time_preference": null, "date_confirmed": null, "time_confirmed": null, "awaiting_confirmation": null}\n\n'
        "Allowed operation values are null, lookup_dates, lookup_slots, and book_appointment.\n"
        "Use slot_updates for any exact slot values you want stored now.\n"
        "Use clear_slots for any slot keys that should be removed now.\n"
        "Use lookup_dates when the service is known and the user gave or changed a date preference that should be validated against available dates.\n"
        "Use lookup_slots when service and date are known and the user picked or implied a date that should move to time selection.\n"
        "Use book_appointment only when the appointment should be submitted now.\n"
        "Set date_confirmed, time_confirmed, and awaiting_confirmation only when you intentionally want to change them."
    )


class ActionDecisionGeneratorFactory:
    def build(self) -> "LlmActionDecisionGenerator":
        provider = os.getenv(
            "ACTION_AGENT_PROVIDER",
            os.getenv("KB_ANSWER_PROVIDER", "openai"),
        ).strip().lower()
        if provider == "openai":
            return OpenAIActionDecisionGenerator.from_env()
        if provider == "azure_openai":
            return AzureOpenAIActionDecisionGenerator.from_env()
        if provider == "gemini":
            return GeminiActionDecisionGenerator.from_env()
        raise ValueError(
            "Unsupported ACTION_AGENT_PROVIDER "
            f"'{provider}'. Use 'openai', 'azure_openai', or 'gemini'."
        )


class LlmActionDecisionGenerator:
    def plan_next_step(
        self,
        context: AppointmentActionPlanningContext,
    ) -> AppointmentActionDecision:
        raise NotImplementedError


class OpenAIActionDecisionGenerator(LlmActionDecisionGenerator):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
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
    def from_env(cls) -> "OpenAIActionDecisionGenerator":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            system_prompt=os.getenv(
                "ACTION_PLANNER_SYSTEM_PROMPT",
                DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
            ),
        )

    def plan_next_step(
        self,
        context: AppointmentActionPlanningContext,
    ) -> AppointmentActionDecision:
        prompt = build_action_planning_prompt(context)
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
            provider_name="OpenAI action planner",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI action planner did not contain choices.")
        content = choices[0].get("message", {}).get("content", "")
        return _parse_decision_content(str(content))


class GeminiActionDecisionGenerator(LlmActionDecisionGenerator):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str = DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
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
    def from_env(cls) -> "GeminiActionDecisionGenerator":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
            system_prompt=os.getenv(
                "ACTION_PLANNER_SYSTEM_PROMPT",
                DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
            ),
        )

    def plan_next_step(
        self,
        context: AppointmentActionPlanningContext,
    ) -> AppointmentActionDecision:
        prompt = build_action_planning_prompt(context)
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
            provider_name="Gemini action planner",
        )
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini action planner did not contain candidates.")
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "\n".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
        return _parse_decision_content(text)

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"


class AzureOpenAIActionDecisionGenerator(LlmActionDecisionGenerator):
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str,
        system_prompt: str = DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
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
    def from_env(cls) -> "AzureOpenAIActionDecisionGenerator":
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            ),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            system_prompt=os.getenv(
                "ACTION_PLANNER_SYSTEM_PROMPT",
                DEFAULT_ACTION_PLANNER_SYSTEM_PROMPT,
            ),
        )

    def plan_next_step(
        self,
        context: AppointmentActionPlanningContext,
    ) -> AppointmentActionDecision:
        prompt = build_action_planning_prompt(context)
        response_payload = post_json(
            url=_build_azure_chat_completions_url(
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
            headers={
                "api-key": self._api_key,
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            provider_name="Azure OpenAI action planner",
        )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Azure OpenAI action planner did not contain choices.")
        content = choices[0].get("message", {}).get("content", "")
        return _parse_decision_content(str(content))


def _parse_decision_content(content: str) -> AppointmentActionDecision:
    json_block_match = re.search(r"\{.*\}", content, re.DOTALL)
    raw_json = json_block_match.group(0) if json_block_match else content
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise RuntimeError("Action planner payload was not a JSON object.")
    operation = _string_or_none(payload.get("operation"))
    if operation not in {None, "lookup_dates", "lookup_slots", "book_appointment"}:
        raise RuntimeError(f"Unsupported action planner operation: {operation}")
    slot_updates = payload.get("slot_updates")
    clear_slots = payload.get("clear_slots")
    return AppointmentActionDecision(
        phase=_string_or_none(payload.get("phase")) or "collecting",
        operation=operation,
        slot_updates=slot_updates if isinstance(slot_updates, dict) else {},
        clear_slots=clear_slots if isinstance(clear_slots, list) else [],
        time_preference=_string_or_none(payload.get("time_preference")),
        date_confirmed=_bool_or_none(payload.get("date_confirmed")),
        time_confirmed=_bool_or_none(payload.get("time_confirmed")),
        awaiting_confirmation=_bool_or_none(payload.get("awaiting_confirmation")),
    )


def _string_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _build_azure_chat_completions_url(
    endpoint: str,
    deployment: str,
    api_version: str,
) -> str:
    quoted_deployment = parse.quote(deployment, safe="")
    query = parse.urlencode({"api-version": api_version})
    return (
        f"{endpoint}/openai/deployments/{quoted_deployment}/chat/completions?{query}"
    )


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip().rstrip("/")


def _require_non_empty(value: str, env_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{env_name} must not be empty.")
    return normalized
