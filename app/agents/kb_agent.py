from __future__ import annotations

from app.agents.contracts import StateAgent
from app.graph.state import ChatState
from app.services.contracts import KnowledgeBaseService


class KnowledgeBaseAgent(StateAgent):
    def __init__(self, knowledge_base_service: KnowledgeBaseService) -> None:
        self._knowledge_base_service = knowledge_base_service

    def execute(self, state: ChatState) -> ChatState:
        answer = self._knowledge_base_service.answer(state)
        return answer.as_state_update()
