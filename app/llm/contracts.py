from __future__ import annotations

from typing import Protocol

from app.services.action_models import (
    AppointmentActionDecision,
    AppointmentActionPlanningContext,
    AppointmentActionReplyContext,
)


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


class ActionDecisionGenerator(Protocol):
    def plan_next_step(
        self,
        context: AppointmentActionPlanningContext,
    ) -> AppointmentActionDecision:
        ...
