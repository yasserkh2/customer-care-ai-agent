from __future__ import annotations

from collections.abc import Iterable


class DefaultConversationHistoryManager:
    def normalize_query(self, query: str) -> str:
        return query.strip()

    def append_user_message(self, history: Iterable[str], message: str) -> list[str]:
        return self._append_message(history, "user", message)

    def append_assistant_message(
        self, history: Iterable[str], message: str
    ) -> list[str]:
        return self._append_message(history, "assistant", message)

    def _append_message(
        self, history: Iterable[str], speaker: str, message: str
    ) -> list[str]:
        normalized_message = message.strip()
        updated_history = list(history)
        if normalized_message:
            updated_history.append(f"{speaker}: {normalized_message}")
        return updated_history
