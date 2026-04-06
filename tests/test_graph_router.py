from __future__ import annotations

import unittest

from app.graph.router import ActiveFlowRouter


class ActiveFlowRouterTests(unittest.TestCase):
    def test_routes_active_appointment_flow_directly_to_action_request(self) -> None:
        router = ActiveFlowRouter()

        route = router({"active_action": "appointment_scheduling"})

        self.assertEqual(route, "action_request")

    def test_routes_to_classify_intent_when_no_active_action_exists(self) -> None:
        router = ActiveFlowRouter()

        route = router({"active_action": None})

        self.assertEqual(route, "classify_intent")


if __name__ == "__main__":
    unittest.main()
