from __future__ import annotations

import unittest

from app.graph.nodes.response import ResponseNode
from app.graph.router import ActiveFlowRouter, GraphRouter, PostTurnRouter, ServiceResultRouter
from app.graph.state import create_initial_state
from app.services.contracts import ConversationHistoryManager
from app.services.escalation import PostTurnEscalationEvaluator
from app.services.history import DefaultConversationHistoryManager
from app.services.models import IntentDecision
from app.services.responses import HumanEscalationService
from app.services.router import DefaultIntentRouter


class StubIntentClassifier:
    def __init__(self, decision: IntentDecision) -> None:
        self._decision = decision

    def classify(self, state):
        return self._decision


class StubAgent:
    def __init__(self, state_update: dict[str, object]) -> None:
        self._state_update = state_update

    def execute(self, state):
        return dict(self._state_update)


class StubHumanEscalationAgent:
    def __init__(self) -> None:
        self._service = HumanEscalationService()

    def execute(self, state):
        return {
            "intent": "human_escalation",
            "handoff_pending": True,
            "active_action": None,
            "appointment_slots": {},
            "missing_slots": [],
            "available_dates": [],
            "date_confirmed": False,
            "available_slots": [],
            "time_confirmed": False,
            "awaiting_confirmation": False,
            "final_response": self._service.build_response(state),
        }


class EscalationFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._history_manager: ConversationHistoryManager = (
            DefaultConversationHistoryManager()
        )
        self._response = ResponseNode(self._history_manager)
        self._intent_router = GraphRouter(DefaultIntentRouter())
        self._active_flow_router = ActiveFlowRouter()
        self._service_result_router = ServiceResultRouter()
        self._post_turn_router = PostTurnRouter()
        self._evaluate_escalation = PostTurnEscalationEvaluator()

    def _run_turn(
        self,
        state,
        intent_decision: IntentDecision,
        kb_state_update: dict[str, object] | None = None,
        action_state_update: dict[str, object] | None = None,
    ):
        classify_intent = StubIntentClassifier(intent_decision)
        kb_answer = StubAgent(kb_state_update or {})
        action_request = StubAgent(action_state_update or {})
        human_escalation = StubHumanEscalationAgent()

        merged_state = {**state, **self._ingest_query(state)}
        active_route = self._active_flow_router(merged_state)

        if active_route == "human_escalation":
            return self._respond_after_handoff(merged_state, human_escalation)
        if active_route == "action_request":
            return self._handle_service_route(merged_state, action_request)

        merged_state = {**merged_state, **classify_intent.classify(merged_state).as_state_update()}
        intent_route = self._intent_router(merged_state)

        if intent_route == "human_escalation":
            return self._respond_after_handoff(merged_state, human_escalation)
        if intent_route == "action_request":
            return self._handle_service_route(merged_state, action_request)

        return self._handle_service_route(merged_state, kb_answer)

    def _handle_service_route(self, state, service_node):
        human_escalation = StubHumanEscalationAgent()

        merged_state = {**state, **service_node.execute(state)}
        service_route = self._service_result_router(merged_state)
        if service_route == "human_escalation":
            return self._respond_after_handoff(merged_state, human_escalation)

        merged_state = {**merged_state, **self._evaluate_escalation.evaluate(merged_state)}
        post_turn_route = self._post_turn_router(merged_state)
        if post_turn_route == "human_escalation":
            return self._respond_after_handoff(merged_state, human_escalation)

        return {**merged_state, **self._response(merged_state)}

    def _respond_after_handoff(self, state, human_escalation):
        merged_state = {**state, **human_escalation.execute(state)}
        return {**merged_state, **self._response(merged_state)}

    def _ingest_query(self, state):
        user_query = self._history_manager.normalize_query(state.get("user_query", ""))
        history = self._history_manager.append_user_message(
            state.get("history", []), user_query
        )
        return {
            "user_query": user_query,
            "history": history,
        }

    def test_explicit_escalation_intent_routes_directly_to_human_escalation(self) -> None:
        state = self._run_turn(
            create_initial_state("I want a human agent"),
            IntentDecision(
                intent="human_escalation",
                confidence=0.98,
                escalation_reason="User requested a human agent.",
            ),
        )

        self.assertTrue(state["handoff_pending"])
        self.assertEqual(state["intent"], "human_escalation")
        self.assertIn("human agent", state["final_response"])

    def test_handoff_pending_forces_next_turn_into_human_escalation(self) -> None:
        state = create_initial_state("still there?")
        state.update(
            {
                "handoff_pending": True,
                "active_action": "appointment_scheduling",
                "awaiting_confirmation": True,
                "date_confirmed": True,
                "time_confirmed": True,
            }
        )

        result = self._run_turn(
            state,
            IntentDecision(intent="kb_query", confidence=0.7),
        )

        self.assertTrue(result["handoff_pending"])
        self.assertIsNone(result["active_action"])
        self.assertFalse(result["awaiting_confirmation"])
        self.assertFalse(result["date_confirmed"])
        self.assertFalse(result["time_confirmed"])

    def test_third_unresolved_kb_turn_routes_to_human_escalation(self) -> None:
        state = create_initial_state("What is the answer?")
        state["failure_count"] = 2

        result = self._run_turn(
            state,
            IntentDecision(intent="kb_query", confidence=0.8),
            kb_state_update={
                "final_response": "I could not find a grounded answer.",
                "turn_outcome": "unresolved",
                "turn_failure_reason": "no_grounded_answer",
            },
        )

        self.assertTrue(result["handoff_pending"])
        self.assertEqual(result["failure_count"], 3)
        self.assertEqual(result["intent"], "human_escalation")
        self.assertIn("repeated attempts", result["final_response"])

    def test_action_failure_with_escalation_reason_routes_to_human_escalation(self) -> None:
        result = self._run_turn(
            create_initial_state("book an appointment"),
            IntentDecision(intent="action_request", confidence=0.9),
            action_state_update={
                "active_action": "appointment_scheduling",
                "final_response": "Action failed.",
                "turn_outcome": "unresolved",
                "turn_failure_reason": "action_extraction_failed",
                "escalation_reason": "I need to transfer this appointment request.",
            },
        )

        self.assertTrue(result["handoff_pending"])
        self.assertIsNone(result["active_action"])
        self.assertEqual(result["intent"], "human_escalation")
        self.assertIn("transfer this conversation", result["final_response"])


if __name__ == "__main__":
    unittest.main()
