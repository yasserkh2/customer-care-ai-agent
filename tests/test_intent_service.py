from __future__ import annotations

import unittest

from app.services.intent import KeywordIntentClassifier


class KeywordIntentClassifierTests(unittest.TestCase):
    def test_active_appointment_flow_stays_routed_to_action_request(self) -> None:
        classifier = KeywordIntentClassifier()

        result = classifier.classify(
            {
                "user_query": "what are the available services",
                "active_action": "appointment_scheduling",
            }
        )

        self.assertEqual(result.intent, "action_request")
        self.assertGreaterEqual(result.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
