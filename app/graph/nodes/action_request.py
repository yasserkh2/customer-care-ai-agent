from app.graph.state import ChatState
from app.services.contracts import ActionRequestService
from app.services.responses import AppointmentRequestService


class ActionRequestNode:
    def __init__(self, action_request_service: ActionRequestService) -> None:
        self._action_request_service = action_request_service

    def __call__(self, state: ChatState) -> ChatState:
        return {
            "final_response": self._action_request_service.build_response(state),
        }


_default_node = ActionRequestNode(AppointmentRequestService())


def action_request(state: ChatState) -> ChatState:
    return _default_node(state)
