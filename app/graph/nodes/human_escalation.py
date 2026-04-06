from app.agents import HumanEscalationAgent
from app.graph.state import ChatState
from app.services.responses import HumanEscalationService


class HumanEscalationNode:
    def __init__(self, agent: HumanEscalationAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        return self._agent.execute(state)


_default_node = HumanEscalationNode(
    HumanEscalationAgent(HumanEscalationService())
)


def human_escalation(state: ChatState) -> ChatState:
    return _default_node(state)
