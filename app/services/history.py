from __future__ import annotations

from collections.abc import Iterable


class DefaultConversationHistoryManager:
    def __init__(
        self,
        summary_trigger_messages: int = 10,
        context_window_tokens: int = 20_000,
        keep_recent_messages: int = 8,
        summary_max_chars: int = 1200,
    ) -> None:
        if summary_trigger_messages <= 0:
            raise ValueError("summary_trigger_messages must be greater than zero.")
        if context_window_tokens <= 0:
            raise ValueError("context_window_tokens must be greater than zero.")
        if keep_recent_messages <= 0:
            raise ValueError("keep_recent_messages must be greater than zero.")
        if summary_max_chars <= 0:
            raise ValueError("summary_max_chars must be greater than zero.")

        self._summary_trigger_messages = summary_trigger_messages
        self._context_window_tokens = context_window_tokens
        self._keep_recent_messages = keep_recent_messages
        self._summary_max_chars = summary_max_chars
        self._summary_prefix = "summary: "

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
        return self._summarize_if_needed(updated_history)

    def _summarize_if_needed(self, history: list[str]) -> list[str]:
        if not history:
            return history

        if (
            len(history) <= self._summary_trigger_messages
            and self._estimate_tokens(history) <= self._context_window_tokens
        ):
            return history

        existing_summary, messages = self._split_existing_summary(history)
        if len(messages) <= self._keep_recent_messages:
            return history

        to_summarize = messages[: -self._keep_recent_messages]
        recent_messages = messages[-self._keep_recent_messages :]
        merged_summary = self._merge_summary(existing_summary, to_summarize)
        if not merged_summary:
            return history
        return [f"{self._summary_prefix}{merged_summary}", *recent_messages]

    def _split_existing_summary(self, history: list[str]) -> tuple[str, list[str]]:
        if history and history[0].startswith(self._summary_prefix):
            return history[0][len(self._summary_prefix) :].strip(), history[1:]
        return "", history

    def _merge_summary(self, existing_summary: str, messages: list[str]) -> str:
        if not messages and existing_summary:
            return existing_summary

        parts: list[str] = []
        if existing_summary:
            parts.append(existing_summary)

        excerpt_parts: list[str] = []
        for item in messages:
            normalized = item.strip()
            if not normalized:
                continue
            if normalized.startswith("user:"):
                label = "User"
                content = normalized.removeprefix("user:").strip()
            elif normalized.startswith("assistant:"):
                label = "Assistant"
                content = normalized.removeprefix("assistant:").strip()
            else:
                label = "Message"
                content = normalized
            excerpt_parts.append(f"{label}: {content}")

        if excerpt_parts:
            parts.append(" | ".join(excerpt_parts))

        combined = " ".join(part for part in parts if part).strip()
        if len(combined) <= self._summary_max_chars:
            return combined
        return combined[-self._summary_max_chars :]

    @staticmethod
    def _estimate_tokens(history: list[str]) -> int:
        # Conservative token estimate: ~1 token per 4 characters.
        char_count = sum(len(item) for item in history)
        return max(1, char_count // 4)
