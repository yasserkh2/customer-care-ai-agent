from __future__ import annotations

from dataclasses import dataclass

from app.agents import AgentFactory, ActionRequestAgent, HumanEscalationAgent, KnowledgeBaseAgent
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
from app.services.knowledge_base import RetrievalKnowledgeBaseService
from app.services.responses import (
    AppointmentRequestService,
    HumanEscalationService,
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
    kb_agent: KnowledgeBaseAgent
    action_agent: ActionRequestAgent
    escalation_agent: HumanEscalationAgent

    @classmethod
    def default(cls) -> "GraphDependencies":
        history_manager = DefaultConversationHistoryManager()
        knowledge_base_service = RetrievalKnowledgeBaseService()
        action_request_service = AppointmentRequestService()
        escalation_service = HumanEscalationService()
        agent_factory = AgentFactory(
            knowledge_base_service=knowledge_base_service,
            action_request_service=action_request_service,
            escalation_service=escalation_service,
        )
        return cls(
            history_manager=history_manager,
            intent_classifier=KeywordIntentClassifier(),
            knowledge_base_service=knowledge_base_service,
            action_request_service=action_request_service,
            escalation_service=escalation_service,
            intent_router=DefaultIntentRouter(),
            kb_agent=agent_factory.build_kb_agent(),
            action_agent=agent_factory.build_action_agent(),
            escalation_agent=agent_factory.build_escalation_agent(),
        )
