from app.agents import HumanEscalationAgent
from app.graph.state import ChatState
from app.observability import get_logger, summarize_state, summarize_update

logger = get_logger("graph.nodes.human_escalation")


class HumanEscalationNode:
    def __init__(self, agent: HumanEscalationAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        logger.info("human_escalation starting: %s", summarize_state(state))
        update = self._agent.execute(state)
        logger.info("human_escalation completed: %s", summarize_update(update))
        return update
