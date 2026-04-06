from __future__ import annotations

from app.graph.state import ChatState
from app.services.models import KnowledgeBaseAnswer


class PlaceholderKnowledgeBaseService:
    def answer(self, state: ChatState) -> KnowledgeBaseAnswer:
        query = state.get("user_query", "")
        return KnowledgeBaseAnswer(
            final_response=(
                "This is a placeholder KB answer path. "
                f"Later we will retrieve grounded context for: '{query}'."
            )
        )


class AppointmentRequestService:
    def build_response(self, state: ChatState) -> str:
        return (
            "I can help with an appointment request. "
            "Please share the service you need, plus your preferred date and time."
        )


class HumanEscalationService:
    def build_response(self, state: ChatState) -> str:
        reason = state.get("escalation_reason") or "This request needs human support."
        return (
            "I need to transfer this conversation to a human agent. "
            "A human agent will follow up with you. "
            f"Reason: {reason}"
        )
