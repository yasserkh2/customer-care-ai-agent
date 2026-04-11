from __future__ import annotations

import unittest

from app.agents.escalation_agent import HumanEscalationAgent
from app.services.responses import HumanEscalationService


class EscalationContactFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved_states: list[dict[str, object]] = []

        def _record(state):
            self.saved_states.append(dict(state))
            return "esc_test_uuid_123"

        self._agent = HumanEscalationAgent(
            HumanEscalationService(),
            escalation_recorder=_record,
        )

    def test_handoff_without_contact_asks_for_name_and_contact_channel(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "I need a human agent",
                "escalation_reason": "User requested a human.",
            }
        )

        self.assertTrue(update["handoff_pending"])
        self.assertIn("Please share your name", update["final_response"])
        self.assertIn("phone number or email", update["final_response"])
        self.assertIsNone(update["escalation_contact_email"])
        self.assertIsNone(update["escalation_contact_phone"])
        self.assertIsNone(update["escalation_case_id"])
        self.assertEqual(len(self.saved_states), 0)

    def test_handoff_uses_existing_escalation_contact_and_confirms_follow_up(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "Please escalate this conversation.",
                "escalation_reason": "Needs human support.",
                "escalation_contact_name": "Yasser",
                "escalation_contact_email": "yasser@example.com",
            }
        )

        self.assertEqual(update["escalation_contact_name"], "Yasser")
        self.assertEqual(update["escalation_contact_email"], "yasser@example.com")
        self.assertEqual(update["escalation_case_id"], "esc_test_uuid_123")
        self.assertEqual(len(self.saved_states), 1)
        self.assertIn("Thanks, Yasser.", update["final_response"])
        self.assertIn("esc_test_uuid_123", update["final_response"])
        self.assertIn("They'll reach out at yasser@example.com shortly.", update["final_response"])

    def test_handoff_uses_existing_llm_extracted_contact(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "please escalate",
                "escalation_reason": "User asked for escalation.",
                "escalation_contact_name": "Yasser Khira",
                "escalation_contact_email": "yasser@company.com",
            }
        )

        self.assertEqual(update["escalation_contact_name"], "Yasser Khira")
        self.assertEqual(update["escalation_contact_email"], "yasser@company.com")
        self.assertEqual(update["escalation_case_id"], "esc_test_uuid_123")
        self.assertIn("They'll reach out at yasser@company.com shortly.", update["final_response"])

    def test_handoff_with_existing_case_id_does_not_persist_again(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "thanks",
                "escalation_reason": "User asked for escalation.",
                "escalation_contact_name": "Yasser",
                "escalation_contact_email": "yasser@example.com",
                "escalation_case_id": "esc_existing_case",
            }
        )

        self.assertEqual(update["escalation_case_id"], "esc_existing_case")
        self.assertEqual(len(self.saved_states), 0)

    def test_handoff_recovers_email_from_user_query_when_llm_email_is_truncated(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "Yasser Khira yasserkhira@gmail.com",
                "escalation_reason": "User requested human support.",
                "escalation_contact_name": "Yasser Khira",
                "escalation_contact_email": "yasserkhira@gmail.c",
            }
        )

        self.assertEqual(update["escalation_contact_email"], "yasserkhira@gmail.com")
        self.assertEqual(update["escalation_case_id"], "esc_test_uuid_123")
        self.assertIn("They'll reach out at yasserkhira@gmail.com shortly.", update["final_response"])

    def test_handoff_reprompts_when_contact_channel_is_invalid(self) -> None:
        update = self._agent.execute(
            {
                "user_query": "Yasser Khira yasserkhira@gmail.c",
                "escalation_reason": "User requested human support.",
                "escalation_contact_name": "Yasser Khira",
                "escalation_contact_email": "yasserkhira@gmail.c",
            }
        )

        self.assertIsNone(update["escalation_contact_email"])
        self.assertIsNone(update["escalation_case_id"])
        self.assertIn("valid phone number or email", update["final_response"])


if __name__ == "__main__":
    unittest.main()
