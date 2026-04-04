from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.graph.state import ChatState
from app.services.models import IntentDecision


@dataclass(frozen=True, slots=True)
class IntentKeywordCatalog:
    action_keywords: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"appointment", "book", "booking", "schedule", "meeting"}
        )
    )
    escalation_keywords: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"human", "agent", "manager", "complaint", "representative"}
        )
    )
    frustration_keywords: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"angry", "frustrated", "upset", "annoyed", "terrible"}
        )
    )


class KeywordIntentClassifier:
    def __init__(self, keyword_catalog: IntentKeywordCatalog | None = None) -> None:
        self._keyword_catalog = keyword_catalog or IntentKeywordCatalog()

    def classify(self, state: ChatState) -> IntentDecision:
        query = state.get("user_query", "")
        normalized_query = query.lower()
        frustration_flag = self._contains_any(
            normalized_query, self._keyword_catalog.frustration_keywords
        )

        if frustration_flag or self._contains_any(
            normalized_query, self._keyword_catalog.escalation_keywords
        ):
            return IntentDecision(
                intent="human_escalation",
                confidence=0.9,
                frustration_flag=frustration_flag,
                escalation_reason=(
                    "User requested help from a human or showed frustration."
                ),
            )

        if self._contains_any(normalized_query, self._keyword_catalog.action_keywords):
            return IntentDecision(
                intent="action_request",
                confidence=0.85,
                frustration_flag=frustration_flag,
            )

        return IntentDecision(
            intent="kb_query",
            confidence=0.65,
            frustration_flag=frustration_flag,
        )

    @staticmethod
    def _contains_any(text: str, keywords: Iterable[str]) -> bool:
        return any(keyword in text for keyword in keywords)
