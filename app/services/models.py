from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.graph.state import ChatState, Intent


@dataclass(frozen=True, slots=True)
class IntentDecision:
    intent: Intent
    confidence: float
    frustration_flag: bool = False
    escalation_reason: str | None = None

    def as_state_update(self) -> ChatState:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "frustration_flag": self.frustration_flag,
            "escalation_reason": self.escalation_reason,
        }


@dataclass(frozen=True, slots=True)
class KnowledgeBaseAnswer:
    final_response: str
    retrieved_context: Sequence[str] = ()

    def as_state_update(self) -> ChatState:
        return {
            "final_response": self.final_response,
            "retrieved_context": list(self.retrieved_context),
        }
