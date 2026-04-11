from __future__ import annotations

import unittest

from app.services.query_rewriting import LlmRetrievalQueryRewriter


class StubRetrievalQueryGenerator:
    def __init__(self, rewritten_query: str) -> None:
        self._rewritten_query = rewritten_query
        self.calls: list[dict[str, object]] = []

    def generate_query(
        self,
        user_query: str,
        conversation_history: list[str],
    ) -> str:
        self.calls.append(
            {
                "user_query": user_query,
                "conversation_history": list(conversation_history),
            }
        )
        return self._rewritten_query


class BrokenRetrievalQueryGenerator:
    def generate_query(
        self,
        user_query: str,
        conversation_history: list[str],
    ) -> str:
        raise RuntimeError("rewriter unavailable")


class LlmRetrievalQueryRewriterTests(unittest.TestCase):
    def test_uses_llm_generated_query(self) -> None:
        generator = StubRetrievalQueryGenerator(
            "What does Credentialing and Provider Maintenance usually include?"
        )
        rewriter = LlmRetrievalQueryRewriter(generator=generator)

        rewritten = rewriter.rewrite(
            query="What This Service Usually Includes",
            history=[
                "user: do Credentialing and Provider Maintenance supports provider enrollment",
                "assistant: Yes, the Credentialing and Provider Maintenance service supports provider enrollment.",
            ],
        )

        self.assertEqual(
            rewritten,
            "What does Credentialing and Provider Maintenance usually include?",
        )
        self.assertEqual(
            generator.calls,
            [
                {
                    "user_query": "What This Service Usually Includes",
                    "conversation_history": [
                        "user: do Credentialing and Provider Maintenance supports provider enrollment",
                        "assistant: Yes, the Credentialing and Provider Maintenance service supports provider enrollment.",
                    ],
                }
            ],
        )

    def test_raises_when_llm_fails(self) -> None:
        rewriter = LlmRetrievalQueryRewriter(
            generator=BrokenRetrievalQueryGenerator(),
        )

        with self.assertRaises(RuntimeError):
            rewriter.rewrite(
                query="When should that be escalated?",
                history=[
                    "user: Tell me about Digital Marketing and Website Services",
                    "assistant: Digital marketing and website services cover website support and visibility work.",
                ],
            )


if __name__ == "__main__":
    unittest.main()
