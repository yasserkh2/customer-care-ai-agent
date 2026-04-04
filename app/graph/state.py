from typing import Any, Literal, TypedDict


Intent = Literal["kb_query", "action_request", "human_escalation", "unknown"]


class ChatState(TypedDict, total=False):
    user_query: str
    intent: Intent
    confidence: float
    entities: dict[str, Any]
    history: list[str]
    failure_count: int
    frustration_flag: bool
    escalation_reason: str | None
    retrieved_context: list[str]
    final_response: str


def create_initial_state(user_query: str) -> ChatState:
    return {
        "user_query": user_query,
        "intent": "unknown",
        "confidence": 0.0,
        "entities": {},
        "history": [],
        "failure_count": 0,
        "frustration_flag": False,
        "escalation_reason": None,
        "retrieved_context": [],
        "final_response": "",
    }
