from app.graph.state import ChatState
from app.services.contracts import ConversationHistoryManager
from app.services.history import DefaultConversationHistoryManager


class ResponseNode:
    def __init__(
        self,
        history_manager: ConversationHistoryManager,
        default_response: str = "I am ready to help.",
    ) -> None:
        self._history_manager = history_manager
        self._default_response = default_response

    def __call__(self, state: ChatState) -> ChatState:
        final_response = state.get("final_response") or self._default_response
        history = self._history_manager.append_assistant_message(
            state.get("history", []), final_response
        )
        return {
            "final_response": final_response,
            "history": history,
        }


_default_node = ResponseNode(DefaultConversationHistoryManager())


def response(state: ChatState) -> ChatState:
    return _default_node(state)
