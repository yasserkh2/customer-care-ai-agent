from __future__ import annotations

import unittest

from app.mock_api.escalation_api import get_saved_escalation, persist_escalation


class MockEscalationPersistenceTests(unittest.TestCase):
    def test_persist_escalation_saves_and_returns_record(self) -> None:
        escalation_id, saved_escalation = persist_escalation(
            {
                "name": "Yasser Khira",
                "email": "yasser@example.com",
                "phone": "",
                "reason": "User requested human support.",
            }
        )
        fetched = get_saved_escalation(escalation_id)

        self.assertTrue(escalation_id.startswith("esc_"))
        self.assertEqual(saved_escalation["escalation_id"], escalation_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "open")
        self.assertEqual(fetched["email"], "yasser@example.com")


if __name__ == "__main__":
    unittest.main()
