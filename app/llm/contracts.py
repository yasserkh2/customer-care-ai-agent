from __future__ import annotations

from typing import Protocol

from app.services.action_models import AppointmentActionReplyContext
from app.services.models import IntentDecision


class AnswerGenerator(Protocol):
    def generate_answer(
        self,
        user_query: str,
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        ...


class ActionReplyGenerator(Protocol):
    def generate_reply(self, context: AppointmentActionReplyContext) -> str:
        ...


class EscalationReplyGenerator(Protocol):
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
        ...


class IntentDecisionGenerator(Protocol):
    def classify_intent(
        self,
        user_query: str,
        conversation_history: list[str],
        active_action: str | None,
        failure_count: int,
    ) -> IntentDecision:
        ...


class RetrievalQueryGenerator(Protocol):
    def generate_query(
        self,
        user_query: str,
        conversation_history: list[str],
    ) -> str:
        ...
