from __future__ import annotations

from app.agents.contracts import StateAgent
from app.graph.state import ChatState
from app.services.contracts import EscalationService


class HumanEscalationAgent(StateAgent):
    def __init__(self, escalation_service: EscalationService) -> None:
        self._escalation_service = escalation_service

    def execute(self, state: ChatState) -> ChatState:
        return {
            "intent": "human_escalation",
            "handoff_pending": True,
            "active_action": None,
            "appointment_slots": {},
            "missing_slots": [],
            "available_dates": [],
            "date_confirmed": False,
            "available_slots": [],
            "time_confirmed": False,
            "awaiting_confirmation": False,
            "final_response": self._escalation_service.build_response(state),
        }
