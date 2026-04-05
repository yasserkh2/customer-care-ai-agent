from __future__ import annotations

from typing import Protocol


class AnswerGenerator(Protocol):
    def generate_answer(
        self,
        user_query: str,
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        ...
