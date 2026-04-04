from __future__ import annotations

from dataclasses import dataclass

from app.services.contracts import (
    ActionRequestService,
    ConversationHistoryManager,
    EscalationService,
    IntentClassifier,
    IntentRouter,
    KnowledgeBaseService,
)
from app.services.history import DefaultConversationHistoryManager
from app.services.intent import KeywordIntentClassifier
from app.services.responses import (
    AppointmentRequestService,
    HumanEscalationService,
    PlaceholderKnowledgeBaseService,
)
from app.services.router import DefaultIntentRouter


@dataclass(frozen=True, slots=True)
class GraphDependencies:
    history_manager: ConversationHistoryManager
    intent_classifier: IntentClassifier
    knowledge_base_service: KnowledgeBaseService
    action_request_service: ActionRequestService
    escalation_service: EscalationService
    intent_router: IntentRouter

    @classmethod
    def default(cls) -> "GraphDependencies":
        history_manager = DefaultConversationHistoryManager()
        return cls(
            history_manager=history_manager,
            intent_classifier=KeywordIntentClassifier(),
            knowledge_base_service=PlaceholderKnowledgeBaseService(),
            action_request_service=AppointmentRequestService(),
            escalation_service=HumanEscalationService(),
            intent_router=DefaultIntentRouter(),
        )
