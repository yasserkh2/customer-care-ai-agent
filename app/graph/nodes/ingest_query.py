from app.graph.state import ChatState
from app.services.contracts import ConversationHistoryManager
from app.services.history import DefaultConversationHistoryManager


class IngestQueryNode:
    def __init__(self, history_manager: ConversationHistoryManager) -> None:
        self._history_manager = history_manager

    def __call__(self, state: ChatState) -> ChatState:
        user_query = self._history_manager.normalize_query(state.get("user_query", ""))
        history = self._history_manager.append_user_message(
            state.get("history", []), user_query
        )
        return {
            "user_query": user_query,
            "history": history,
        }


_default_node = IngestQueryNode(DefaultConversationHistoryManager())


def ingest_query(state: ChatState) -> ChatState:
    return _default_node(state)
