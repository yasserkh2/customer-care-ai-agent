from app.agents import KnowledgeBaseAgent
from app.graph.state import ChatState
from app.services.knowledge_base import RetrievalKnowledgeBaseService


class KnowledgeBaseAnswerNode:
    def __init__(self, agent: KnowledgeBaseAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        return self._agent.execute(state)


_default_node = KnowledgeBaseAnswerNode(
    KnowledgeBaseAgent(RetrievalKnowledgeBaseService())
)


def kb_answer(state: ChatState) -> ChatState:
    return _default_node(state)
