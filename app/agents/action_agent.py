from __future__ import annotations

from app.agents.contracts import StateAgent
from app.graph.state import ChatState
from app.services.contracts import ActionRequestService


class ActionRequestAgent(StateAgent):
    def __init__(self, action_request_service: ActionRequestService) -> None:
        self._action_request_service = action_request_service

    def execute(self, state: ChatState) -> ChatState:
        return self._action_request_service.handle_turn(state)
