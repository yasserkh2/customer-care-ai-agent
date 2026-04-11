from __future__ import annotations

import unittest

from app.services.models import IntentDecision, KnowledgeBaseAnswer


class IntentDecisionModelTests(unittest.TestCase):
    def test_state_update_keeps_escalation_fields_for_human_handoff(self) -> None:
        update = IntentDecision(
            intent="human_escalation",
            confidence=0.97,
            frustration_flag=True,
            escalation_reason="User requested a human agent.",
            escalation_contact_name="Yasser Khira",
            escalation_contact_email="yasser@example.com",
        ).as_state_update()

        self.assertEqual(update["intent"], "human_escalation")
        self.assertEqual(update["confidence"], 0.97)
        self.assertTrue(update["frustration_flag"])
        self.assertEqual(update["escalation_reason"], "User requested a human agent.")
        self.assertEqual(update["escalation_contact_name"], "Yasser Khira")
        self.assertEqual(update["escalation_contact_email"], "yasser@example.com")
        self.assertIsNone(update["escalation_contact_phone"])

    def test_state_update_clears_escalation_reason_for_non_escalation_intent(self) -> None:
        update = IntentDecision(
            intent="kb_query",
            confidence=0.82,
            frustration_flag=False,
            escalation_reason="should not be forwarded",
            escalation_contact_name="Yasser Khira",
            escalation_contact_email="yasser@example.com",
            escalation_contact_phone="+1 555 123 4567",
        ).as_state_update()

        self.assertEqual(update["intent"], "kb_query")
        self.assertIsNone(update["escalation_reason"])
        self.assertEqual(update["escalation_contact_name"], "Yasser Khira")
        self.assertEqual(update["escalation_contact_email"], "yasser@example.com")
        self.assertEqual(update["escalation_contact_phone"], "+1 555 123 4567")


class KnowledgeBaseAnswerModelTests(unittest.TestCase):
    def test_state_update_includes_escalation_reason(self) -> None:
        update = KnowledgeBaseAnswer(
            final_response="Action needed.",
            retrieval_query="help",
            turn_outcome="unresolved",
            turn_failure_reason="requires_human",
            escalation_reason="This question needs a specialist.",
        ).as_state_update()

        self.assertEqual(update["escalation_reason"], "This question needs a specialist.")


if __name__ == "__main__":
    unittest.main()
