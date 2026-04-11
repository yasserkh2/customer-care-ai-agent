from __future__ import annotations

import unittest

from app.services.responses import HumanEscalationService


class _StubEscalationReplyGenerator:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[dict[str, object]] = []

    def generate_reply(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.reply


class _FailingEscalationReplyGenerator:
    def generate_reply(self, **kwargs) -> str:
        raise RuntimeError("generation failed")


class EscalationResponseGenerationTests(unittest.TestCase):
    def test_uses_llm_generated_handoff_reply_when_available(self) -> None:
        generator = _StubEscalationReplyGenerator(
            "Thanks, Yasser. I've escalated this and our team will call you shortly."
        )
        service = HumanEscalationService(escalation_reply_generator=generator)
        state = {
            "user_query": "i donot like speaking with ai",
            "history": [
                "user: Hi",
                "assistant: Hello! How can I help?",
                "user: i donot like speaking with ai",
            ],
            "escalation_reason": "user does not want to speak with AI",
            "escalation_contact_name": "Yasser",
            "escalation_contact_email": "yasserkhira@gmail.com",
            "escalation_case_id": "esc_123",
        }

        response = service.build_response(state)

        self.assertEqual(
            response,
            "Thanks, Yasser. I've escalated this and our team will call you shortly.",
        )
        self.assertEqual(len(generator.calls), 1)
        self.assertFalse(bool(generator.calls[0]["requires_contact"]))
        self.assertEqual(generator.calls[0]["escalation_case_id"], "esc_123")

    def test_falls_back_to_template_when_llm_generation_fails(self) -> None:
        service = HumanEscalationService(
            escalation_reply_generator=_FailingEscalationReplyGenerator()
        )
        state = {
            "user_query": "i donot like speaking with ai",
            "history": [],
            "escalation_reason": "user does not want to speak with AI",
        }

        response = service.build_response(state)

        self.assertIn("I need to transfer this conversation to a human agent.", response)
        self.assertIn("Please share your name", response)


if __name__ == "__main__":
    unittest.main()
