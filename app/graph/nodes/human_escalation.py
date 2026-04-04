from app.graph.state import ChatState
from app.services.contracts import EscalationService
from app.services.responses import HumanEscalationService


class HumanEscalationNode:
    def __init__(self, escalation_service: EscalationService) -> None:
        self._escalation_service = escalation_service

    def __call__(self, state: ChatState) -> ChatState:
        return {
            "final_response": self._escalation_service.build_response(state),
        }


_default_node = HumanEscalationNode(HumanEscalationService())


def human_escalation(state: ChatState) -> ChatState:
    return _default_node(state)
