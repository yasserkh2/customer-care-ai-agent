from __future__ import annotations

from time import perf_counter

from app.graph.state import ChatState
from app.llm.contracts import IntentDecisionGenerator
from app.llm.intent_factory import IntentDecisionGeneratorFactory
from app.observability import get_logger, summarize_state
from app.services.models import IntentDecision

logger = get_logger("services.intent")


class LlmIntentClassifier:
    def __init__(
        self,
        decision_generator: IntentDecisionGenerator | None = None,
    ) -> None:
        if decision_generator is not None:
            self._decision_generator = decision_generator
        else:
            self._decision_generator = self._build_generator()

    def classify(self, state: ChatState) -> IntentDecision:
        if self._decision_generator is None:
            logger.info("llm intent classifier unavailable, using static fallback")
            return self._fallback_decision()

        try:
            logger.info("llm intent classifier evaluating state=%s", summarize_state(state))
            classify_start = perf_counter()
            decision = self._decision_generator.classify_intent(
                user_query=state.get("user_query", ""),
                conversation_history=list(state.get("history", [])),
                active_action=state.get("active_action"),
                failure_count=int(state.get("failure_count", 0)),
            )
            classify_ms = (perf_counter() - classify_start) * 1000
            logger.info(
                "llm intent classifier chose intent=%s confidence=%s frustration=%s latency_ms=%.1f",
                decision.intent,
                decision.confidence,
                decision.frustration_flag,
                classify_ms,
            )
            return decision
        except Exception as exc:
            logger.exception("llm intent classifier failed, using static fallback: %s", exc)
            return self._fallback_decision()

    @staticmethod
    def _build_generator() -> IntentDecisionGenerator | None:
        try:
            return IntentDecisionGeneratorFactory().build()
        except Exception:
            return None

    @staticmethod
    def _fallback_decision() -> IntentDecision:
        return IntentDecision(
            intent="kb_query",
            confidence=0.0,
            frustration_flag=False,
            escalation_reason=None,
        )
