from __future__ import annotations

import unittest

from app.services.intent import LlmIntentClassifier
from app.services.models import IntentDecision


class StubIntentDecisionGenerator:
    def __init__(self, decision: IntentDecision) -> None:
        self._decision = decision
        self.calls: list[dict[str, object]] = []

    def classify_intent(
        self,
        user_query: str,
        conversation_history: list[str],
        active_action: str | None,
        failure_count: int,
    ) -> IntentDecision:
        self.calls.append(
            {
                "user_query": user_query,
                "conversation_history": list(conversation_history),
                "active_action": active_action,
                "failure_count": failure_count,
            }
        )
        return self._decision


class FailingIntentDecisionGenerator:
    def classify_intent(
        self,
        user_query: str,
        conversation_history: list[str],
        active_action: str | None,
        failure_count: int,
    ) -> IntentDecision:
        raise RuntimeError("intent classifier offline")


class LlmIntentClassifierTests(unittest.TestCase):
    def test_uses_llm_decision_when_generator_succeeds(self) -> None:
        generator = StubIntentDecisionGenerator(
            IntentDecision(
                intent="human_escalation",
                confidence=0.97,
                frustration_flag=True,
                escalation_reason="User asked for a supervisor.",
            )
        )
        classifier = LlmIntentClassifier(decision_generator=generator)

        result = classifier.classify(
            {
                "user_query": "I want a supervisor",
                "history": ["user: hi", "assistant: hello"],
                "active_action": "appointment_scheduling",
                "failure_count": 2,
            }
        )

        self.assertEqual(result.intent, "human_escalation")
        self.assertTrue(result.frustration_flag)
        self.assertEqual(result.escalation_reason, "User asked for a supervisor.")
        self.assertEqual(generator.calls[0]["failure_count"], 2)
        self.assertEqual(
            generator.calls[0]["conversation_history"],
            ["user: hi", "assistant: hello"],
        )

    def test_uses_llm_general_conversation_decision_when_generator_succeeds(self) -> None:
        generator = StubIntentDecisionGenerator(
            IntentDecision(
                intent="general_conversation",
                confidence=0.88,
                frustration_flag=False,
                escalation_reason=None,
            )
        )
        classifier = LlmIntentClassifier(decision_generator=generator)

        result = classifier.classify(
            {
                "user_query": "hi there",
                "history": ["user: hi"],
                "active_action": None,
                "failure_count": 0,
            }
        )

        self.assertEqual(result.intent, "general_conversation")

    def test_uses_llm_human_escalation_for_direct_human_request(self) -> None:
        generator = StubIntentDecisionGenerator(
            IntentDecision(
                intent="human_escalation",
                confidence=0.96,
                frustration_flag=False,
                escalation_reason="User directly asked to speak with a human agent.",
            )
        )
        classifier = LlmIntentClassifier(decision_generator=generator)

        result = classifier.classify(
            {
                "user_query": "Please connect me with a human agent.",
                "history": [],
                "active_action": None,
                "failure_count": 0,
            }
        )

        self.assertEqual(result.intent, "human_escalation")
        self.assertGreaterEqual(result.confidence, 0.96)
        self.assertEqual(
            result.escalation_reason,
            "User directly asked to speak with a human agent.",
        )

    def test_uses_llm_human_escalation_for_confusion_and_rubbish_signal(self) -> None:
        generator = StubIntentDecisionGenerator(
            IntentDecision(
                intent="human_escalation",
                confidence=0.93,
                frustration_flag=True,
                escalation_reason="User could not understand the assistant and asked for better support.",
            )
        )
        classifier = LlmIntentClassifier(decision_generator=generator)

        result = classifier.classify(
            {
                "user_query": "I cannot understand this bot, the response is rubbish.",
                "history": [],
                "active_action": None,
                "failure_count": 0,
            }
        )

        self.assertEqual(result.intent, "human_escalation")
        self.assertTrue(result.frustration_flag)
        self.assertEqual(
            result.escalation_reason,
            "User could not understand the assistant and asked for better support.",
        )

    def test_fallback_uses_static_kb_decision_when_generator_fails_even_for_escalation_wording(self) -> None:
        classifier = LlmIntentClassifier(
            decision_generator=FailingIntentDecisionGenerator()
        )

        result = classifier.classify(
            {
                "user_query": "i need to escilate",
            }
        )

        self.assertEqual(result.intent, "kb_query")
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.frustration_flag)
        self.assertIsNone(result.escalation_reason)

    def test_fallback_uses_static_kb_decision_for_neutral_query_when_generator_fails(self) -> None:
        classifier = LlmIntentClassifier(
            decision_generator=FailingIntentDecisionGenerator()
        )

        result = classifier.classify(
            {
                "user_query": "What services do you offer?",
            }
        )

        self.assertEqual(result.intent, "kb_query")
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.frustration_flag)
        self.assertIsNone(result.escalation_reason)


if __name__ == "__main__":
    unittest.main()
