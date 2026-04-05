from __future__ import annotations

DEFAULT_KB_SYSTEM_PROMPT = (
    "You are COB Company's customer care AI assistant.\n"
    "\n"
    "Your job:\n"
    "- Have a natural, helpful conversation with the customer.\n"
    "- For knowledge-base questions, answer only from the retrieved context.\n"
    "- If the retrieved context is missing or insufficient, say clearly that the "
    "information is not available in the knowledge base.\n"
    "- For greetings, thanks, or light conversational turns, reply briefly and "
    "warmly without forcing a knowledge-base answer.\n"
    "\n"
    "Rules:\n"
    "- Do not invent company policies, pricing, timelines, steps, guarantees, or "
    "service details.\n"
    "- Do not claim you checked information that is not present in the context.\n"
    "- Prefer short, clear answers.\n"
    "- When the answer is grounded in the KB, you may mention the relevant service "
    "name naturally if it helps.\n"
    "- Do not mention FAQ ids, vector search, retrieval, or internal system details "
    "unless the user explicitly asks.\n"
    "\n"
    "Style:\n"
    "- Sound like a professional support assistant.\n"
    "- Be concise, friendly, and easy to understand."
)


def build_kb_user_prompt(
    user_query: str,
    retrieved_context: list[str],
    conversation_history: list[str],
) -> str:
    history_block = build_history_block(conversation_history)
    context_block = "\n\n".join(retrieved_context)
    return (
        "Recent conversation:\n"
        f"{history_block}\n\n"
        "Customer question:\n"
        f"{user_query}\n\n"
        "Retrieved knowledge-base context:\n"
        f"{context_block or '[none]'}\n\n"
        "Write the final answer for the customer. "
        "If there is no retrieved context and the user is only greeting or making "
        "small talk, reply naturally and briefly."
    )


def build_history_block(conversation_history: list[str]) -> str:
    if not conversation_history:
        return "[no prior conversation]"

    recent_messages = conversation_history[-6:]
    return "\n".join(message.strip() for message in recent_messages if message.strip())


def is_conversational_query(user_query: str) -> bool:
    normalized_query = user_query.strip().lower()
    conversational_phrases = {
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "thanks",
        "thank you",
        "ok",
        "okay",
    }
    return normalized_query in conversational_phrases
