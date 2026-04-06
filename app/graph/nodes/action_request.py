from app.agents import ActionRequestAgent
from app.graph.state import ChatState
from app.services.responses import AppointmentRequestService


class ActionRequestNode:
    def __init__(self, agent: ActionRequestAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        return self._agent.execute(state)


_default_node = ActionRequestNode(ActionRequestAgent(AppointmentRequestService()))


def action_request(state: ChatState) -> ChatState:
    return _default_node(state)
