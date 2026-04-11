from __future__ import annotations

import unittest

from app.services.history import DefaultConversationHistoryManager


class DefaultConversationHistoryManagerTests(unittest.TestCase):
    def test_appends_without_summary_below_threshold(self) -> None:
        manager = DefaultConversationHistoryManager(summary_trigger_messages=10)
        history: list[str] = []
        history = manager.append_user_message(history, "hello")
        history = manager.append_assistant_message(history, "hi there")

        self.assertEqual(history, ["user: hello", "assistant: hi there"])

    def test_summarizes_when_message_count_exceeds_threshold(self) -> None:
        manager = DefaultConversationHistoryManager(
            summary_trigger_messages=10,
            keep_recent_messages=8,
        )
        history: list[str] = []
        for index in range(11):
            history = manager.append_user_message(history, f"message {index}")

        self.assertEqual(len(history), 9)
        self.assertTrue(history[0].startswith("summary: "))
        self.assertEqual(history[1:], [f"user: message {index}" for index in range(3, 11)])

    def test_summarizes_when_context_window_is_exceeded(self) -> None:
        manager = DefaultConversationHistoryManager(
            summary_trigger_messages=100,
            context_window_tokens=50,
            keep_recent_messages=2,
        )
        history: list[str] = []
        history = manager.append_user_message(history, "a" * 120)
        history = manager.append_assistant_message(history, "b" * 120)
        history = manager.append_user_message(history, "c" * 120)

        self.assertEqual(len(history), 3)
        self.assertTrue(history[0].startswith("summary: "))
        self.assertEqual(history[1], f"assistant: {'b' * 120}")
        self.assertEqual(history[2], f"user: {'c' * 120}")


if __name__ == "__main__":
    unittest.main()
