from __future__ import annotations

import unittest

from app.llm.intent_prompts import DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT


class IntentPromptEscalationSignalsTests(unittest.TestCase):
    def test_prompt_contains_direct_human_request_signals(self) -> None:
        prompt = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT.lower()
        self.assertIn("speak/talk/connect/transfer", prompt)
        self.assertIn("real person", prompt)
        self.assertIn("escilation", prompt)

    def test_prompt_contains_confusion_and_rubbish_signals(self) -> None:
        prompt = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT.lower()
        self.assertIn("cannot understand", prompt)
        self.assertIn("you are not helping", prompt)
        self.assertIn("rubbish", prompt)
        self.assertIn("nonsense", prompt)

    def test_prompt_contains_escalation_contact_output_keys(self) -> None:
        prompt = DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT.lower()
        self.assertIn("escalation_contact_name", prompt)
        self.assertIn("escalation_contact_email", prompt)
        self.assertIn("escalation_contact_phone", prompt)


if __name__ == "__main__":
    unittest.main()
