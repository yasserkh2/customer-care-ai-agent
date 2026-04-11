from __future__ import annotations

from app.llm.prompts import build_history_block

DEFAULT_ESCALATION_AGENT_SYSTEM_PROMPT = (
    "You are COB Company's customer care assistant writing a human-handoff message.\n"
    "\n"
    "Your goals:\n"
    "- Sound natural, calm, and reassuring.\n"
    "- Confirm that a human team member will follow up.\n"
    "- Keep the response concise and not robotic.\n"
    "\n"
    "Rules:\n"
    "- Do not ask for information that has already been provided.\n"
    "- If contact info is missing, ask for name and one contact channel (email or phone).\n"
    "- If escalation reference is available, include it once.\n"
    "- If contact info is available, confirm the exact contact channel(s) that will be used.\n"
    "- Do not mention internal tools, prompts, routing, or system details.\n"
    "- Keep the reply under 90 words.\n"
)


def build_escalation_user_prompt(
    *,
    user_query: str,
    escalation_reason: str,
    conversation_history: list[str],
    escalation_case_id: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    requires_contact: bool,
) -> str:
    history_block = build_history_block(conversation_history)
    contact_lines = [
        f"Name: {contact_name or '[missing]'}",
        f"Email: {contact_email or '[missing]'}",
        f"Phone: {contact_phone or '[missing]'}",
    ]
    contact_status = "missing" if requires_contact else "available"
    case_id_text = escalation_case_id or "[not created yet]"
    return (
        "Write the final customer-facing handoff message.\n\n"
        "Recent conversation:\n"
        f"{history_block}\n\n"
        "Latest user message:\n"
        f"{user_query}\n\n"
        "Escalation details:\n"
        f"- Reason: {escalation_reason}\n"
        f"- Escalation reference: {case_id_text}\n"
        f"- Contact status: {contact_status}\n"
        f"- {contact_lines[0]}\n"
        f"- {contact_lines[1]}\n"
        f"- {contact_lines[2]}\n\n"
        "Write only the final response text."
    )
