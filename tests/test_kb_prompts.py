from __future__ import annotations

import unittest

from app.llm.prompts import DEFAULT_KB_SYSTEM_PROMPT, build_kb_user_prompt


class KnowledgeBasePromptTests(unittest.TestCase):
    def test_system_prompt_includes_long_conversation_and_confusion_guidance(self) -> None:
        self.assertIn(
            "If the conversation becomes too long without clear progress",
            DEFAULT_KB_SYSTEM_PROMPT,
        )
        self.assertIn(
            "If the user sounds confused or says the responses are unclear",
            DEFAULT_KB_SYSTEM_PROMPT,
        )

    def test_user_prompt_includes_escalation_guidance_for_long_or_confused_threads(self) -> None:
        prompt = build_kb_user_prompt(
            user_query="I still do not understand",
            retrieved_context=["Document: doc_1\nText: sample"],
            conversation_history=["user: hi", "assistant: hello"],
        )
        self.assertIn(
            "If the conversation is getting long without progress or the user sounds confused",
            prompt,
        )
        self.assertIn("offer a meeting or human escalation as a next step", prompt)


if __name__ == "__main__":
    unittest.main()
