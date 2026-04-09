from app.agents import ActionRequestAgent
from app.graph.state import ChatState
from app.observability import get_logger, summarize_state, summarize_update

logger = get_logger("graph.nodes.action_request")


class ActionRequestNode:
    def __init__(self, agent: ActionRequestAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        logger.info("action_request starting: %s", summarize_state(state))
        update = self._agent.execute(state)
        logger.info("action_request completed: %s", summarize_update(update))
        return update
