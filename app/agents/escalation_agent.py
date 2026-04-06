from __future__ import annotations

from app.agents.contracts import StateAgent
from app.graph.state import ChatState
from app.services.contracts import EscalationService


class HumanEscalationAgent(StateAgent):
    def __init__(self, escalation_service: EscalationService) -> None:
        self._escalation_service = escalation_service

    def execute(self, state: ChatState) -> ChatState:
        return {
            "final_response": self._escalation_service.build_response(state),
        }
