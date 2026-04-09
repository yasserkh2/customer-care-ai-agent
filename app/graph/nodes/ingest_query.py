from app.observability import get_logger, summarize_update
from app.graph.state import ChatState
from app.services.contracts import ConversationHistoryManager

logger = get_logger("graph.nodes.ingest_query")


class IngestQueryNode:
    def __init__(self, history_manager: ConversationHistoryManager) -> None:
        self._history_manager = history_manager

    def __call__(self, state: ChatState) -> ChatState:
        user_query = self._history_manager.normalize_query(state.get("user_query", ""))
        history = self._history_manager.append_user_message(
            state.get("history", []), user_query
        )
        update = {
            "user_query": user_query,
            "history": history,
        }
        logger.info("ingest_query completed: %s", summarize_update(update))
        return update
