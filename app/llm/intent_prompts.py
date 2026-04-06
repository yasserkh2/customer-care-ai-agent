from __future__ import annotations

import json


DEFAULT_INTENT_CLASSIFIER_SYSTEM_PROMPT = (
    "You classify customer-care chat turns into one of three intents. "
    "Return JSON only.\n"
    "\n"
    "Valid intents:\n"
    '- "kb_query" for questions asking for information or explanations.\n'
    '- "action_request" for requests to start or continue a supported process such as appointment scheduling.\n'
    '- "human_escalation" when the user asks for a human, asks to escalate, sounds angry or frustrated, shows repeated failure, the bot is clearly not helping, or the case should be handled by a person.\n'
    "\n"
    "Rules:\n"
    "- If an action flow is already active, keep the intent as action_request unless the user clearly wants a human agent or escalation.\n"
    "- Treat words such as escalate, escalation, escilate, transfer, handoff, supervisor, human, agent, representative, or support as strong escalation signals when used as a request for a person.\n"
    "- Set frustration_flag to true when the user sounds angry, upset, frustrated, or says the bot is not helping.\n"
    "- Set escalation_reason only when intent is human_escalation.\n"
    "- Confidence must be a number between 0 and 1.\n"
    "- Do not include any keys other than the required JSON keys.\n"
)


def build_intent_classifier_prompt(
    user_query: str,
    conversation_history: list[str],
    active_action: str | None,
    failure_count: int,
) -> str:
    history_block = "\n".join(conversation_history[-6:]) or "[no prior conversation]"
    return (
        "Classify the latest customer turn.\n\n"
        "Recent conversation:\n"
        f"{history_block}\n\n"
        "Active action:\n"
        f"{active_action or '[none]'}\n\n"
        "Current failure count:\n"
        f"{failure_count}\n\n"
        "Latest user message:\n"
        f"{user_query}\n\n"
        "Return valid JSON with exactly these keys:\n"
        '{"intent": "kb_query", "confidence": 0.0, "frustration_flag": false, "escalation_reason": null}'
    )


def build_history_block(conversation_history: list[str]) -> str:
    return "\n".join(message.strip() for message in conversation_history[-6:] if message.strip()) or "[no prior conversation]"


def parse_intent_decision_payload(payload: dict[str, object]) -> dict[str, object]:
    intent = str(payload.get("intent", "")).strip()
    if intent not in {"kb_query", "action_request", "human_escalation"}:
        raise RuntimeError("Intent classification payload contained an invalid intent.")

    confidence_value = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence_value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Intent classification payload contained an invalid confidence.") from exc

    confidence = max(0.0, min(1.0, confidence))
    frustration_flag = bool(payload.get("frustration_flag", False))
    escalation_reason = payload.get("escalation_reason")
    if escalation_reason is not None:
        escalation_reason = str(escalation_reason).strip() or None

    return {
        "intent": intent,
        "confidence": confidence,
        "frustration_flag": frustration_flag,
        "escalation_reason": escalation_reason,
    }


def build_intent_classifier_debug_payload(
    user_query: str,
    conversation_history: list[str],
    active_action: str | None,
    failure_count: int,
) -> str:
    return json.dumps(
        {
            "user_query": user_query,
            "conversation_history": conversation_history[-6:],
            "active_action": active_action,
            "failure_count": failure_count,
        },
        sort_keys=True,
    )
