from app.graph.state import ChatState
from app.services.contracts import KnowledgeBaseService
from app.services.responses import PlaceholderKnowledgeBaseService


class KnowledgeBaseAnswerNode:
    def __init__(self, knowledge_base_service: KnowledgeBaseService) -> None:
        self._knowledge_base_service = knowledge_base_service

    def __call__(self, state: ChatState) -> ChatState:
        answer = self._knowledge_base_service.answer(state)
        return answer.as_state_update()


_default_node = KnowledgeBaseAnswerNode(PlaceholderKnowledgeBaseService())


def kb_answer(state: ChatState) -> ChatState:
    return _default_node(state)
