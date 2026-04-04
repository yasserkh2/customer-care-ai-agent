from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from app.graph.state import ChatState
from app.services.models import IntentDecision, KnowledgeBaseAnswer


class ConversationHistoryManager(Protocol):
    def normalize_query(self, query: str) -> str:
        ...

    def append_user_message(self, history: Iterable[str], message: str) -> list[str]:
        ...

    def append_assistant_message(
        self, history: Iterable[str], message: str
    ) -> list[str]:
        ...


class IntentClassifier(Protocol):
    def classify(self, state: ChatState) -> IntentDecision:
        ...


class IntentRouter(Protocol):
    def route(self, state: ChatState) -> str:
        ...


class KnowledgeBaseService(Protocol):
    def answer(self, state: ChatState) -> KnowledgeBaseAnswer:
        ...


class ActionRequestService(Protocol):
    def build_response(self, state: ChatState) -> str:
        ...


class EscalationService(Protocol):
    def build_response(self, state: ChatState) -> str:
        ...
