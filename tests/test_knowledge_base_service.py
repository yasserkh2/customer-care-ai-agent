from __future__ import annotations

import unittest

from app.services.knowledge_base import RetrievalKnowledgeBaseService
from vector_db.models import VectorSearchMatch


class StubEmbeddingGenerator:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.queries: list[str] = []

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return list(self._vector)


class StubVectorSearcher:
    def __init__(self, matches: list[VectorSearchMatch]) -> None:
        self._matches = matches
        self.calls: list[dict[str, object]] = []

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        with_vectors: bool = False,
    ) -> list[VectorSearchMatch]:
        self.calls.append(
            {
                "query_vector": list(query_vector),
                "limit": limit,
                "with_vectors": with_vectors,
            }
        )
        return list(self._matches)


class StubAnswerGenerator:
    def __init__(self, answer: str) -> None:
        self._answer = answer
        self.calls: list[dict[str, object]] = []

    def generate_answer(
        self,
        user_query: str,
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        self.calls.append(
            {
                "user_query": user_query,
                "retrieved_context": list(retrieved_context),
                "conversation_history": list(conversation_history),
            }
        )
        return self._answer


class BrokenVectorSearcher:
    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        with_vectors: bool = False,
    ) -> list[VectorSearchMatch]:
        raise RuntimeError("Qdrant is unavailable.")


class BrokenAnswerGenerator:
    def generate_answer(
        self,
        user_query: str,
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        raise RuntimeError("Generation failed.")


class RetrievalKnowledgeBaseServiceTests(unittest.TestCase):
    def test_returns_grounded_generated_answer_and_context(self) -> None:
        embedding_generator = StubEmbeddingGenerator([0.1, 0.2, 0.3])
        searcher = StubVectorSearcher(
            [
                VectorSearchMatch(
                    point_id="point-1",
                    record_id="faq_001_chunk_0001",
                    score=0.93,
                    payload={
                        "faq_id": "faq_001",
                        "category": "credentialing",
                        "service_name": "Credentialing",
                        "text": (
                            "Question: What does credentialing include?\n"
                            "Answer: Credentialing includes primary source "
                            "verification and application review.\n"
                            "Service: Credentialing"
                        ),
                    },
                ),
                VectorSearchMatch(
                    point_id="point-2",
                    record_id="faq_010_chunk_0001",
                    score=0.71,
                    payload={
                        "faq_id": "faq_010",
                        "category": "enrollment",
                        "service_name": "Enrollment",
                        "text": (
                            "Question: How long does enrollment take?\n"
                            "Answer: Enrollment timelines vary by payer.\n"
                            "Service: Enrollment"
                        ),
                    },
                ),
            ]
        )
        answer_generator = StubAnswerGenerator(
            "Credentialing includes primary source verification and application "
            "review. This answer is based on the retrieved FAQ context."
        )
        service = RetrievalKnowledgeBaseService(
            embedding_generator=embedding_generator,
            searcher=searcher,
            answer_generator=answer_generator,
            retrieval_limit=2,
        )

        result = service.answer({"user_query": "What does credentialing include?"})

        self.assertEqual(
            result.final_response,
            "Credentialing includes primary source verification and application "
            "review. This answer is based on the retrieved FAQ context.",
        )
        self.assertEqual(
            result.retrieved_context[0],
            "FAQ: faq_001\n"
            "Score: 0.9300\n"
            "Category: credentialing\n"
            "Service: Credentialing\n"
            "Question: What does credentialing include?\n"
            "Answer: Credentialing includes primary source verification and "
            "application review.",
        )
        self.assertEqual(embedding_generator.queries, ["What does credentialing include?"])
        self.assertEqual(
            searcher.calls,
            [
                {
                    "query_vector": [0.1, 0.2, 0.3],
                    "limit": 2,
                    "with_vectors": False,
                }
            ],
        )
        self.assertEqual(answer_generator.calls[0]["user_query"], "What does credentialing include?")
        self.assertEqual(len(answer_generator.calls[0]["retrieved_context"]), 2)
        self.assertEqual(answer_generator.calls[0]["conversation_history"], [])

    def test_falls_back_to_extractive_answer_when_generation_fails(self) -> None:
        service = RetrievalKnowledgeBaseService(
            embedding_generator=StubEmbeddingGenerator([1.0]),
            searcher=StubVectorSearcher(
                [
                    VectorSearchMatch(
                        point_id="point-1",
                        record_id="faq_001_chunk_0001",
                        score=0.93,
                        payload={
                            "faq_id": "faq_001",
                            "category": "credentialing",
                            "service_name": "Credentialing",
                            "text": (
                                "Question: What does credentialing include?\n"
                                "Answer: Credentialing includes primary source "
                                "verification and application review.\n"
                                "Service: Credentialing"
                            ),
                        },
                    )
                ]
            ),
            answer_generator=BrokenAnswerGenerator(),
        )

        result = service.answer({"user_query": "What does credentialing include?"})

        self.assertEqual(
            result.final_response,
            "Credentialing includes primary source verification and application "
            "review.\n\nService: Credentialing | Source: FAQ faq_001",
        )

    def test_returns_no_match_message_when_search_is_empty(self) -> None:
        service = RetrievalKnowledgeBaseService(
            embedding_generator=StubEmbeddingGenerator([1.0]),
            searcher=StubVectorSearcher([]),
            answer_generator=StubAnswerGenerator("unused"),
        )

        result = service.answer({"user_query": "Do you offer weekend support?"})

        self.assertIn("could not find a grounded answer", result.final_response)
        self.assertEqual(list(result.retrieved_context), [])

    def test_returns_unavailable_message_when_retrieval_fails(self) -> None:
        service = RetrievalKnowledgeBaseService(
            embedding_generator=StubEmbeddingGenerator([1.0]),
            searcher=BrokenVectorSearcher(),
            answer_generator=StubAnswerGenerator("unused"),
        )

        result = service.answer({"user_query": "What is the status?"})

        self.assertIn("could not access the knowledge base", result.final_response)
        self.assertEqual(list(result.retrieved_context), [])

    def test_greeting_uses_conversational_generation_without_retrieval(self) -> None:
        embedding_generator = StubEmbeddingGenerator([1.0])
        searcher = StubVectorSearcher([])
        answer_generator = StubAnswerGenerator(
            "Hello! How can I help you with COB Company's services or policies today?"
        )
        service = RetrievalKnowledgeBaseService(
            embedding_generator=embedding_generator,
            searcher=searcher,
            answer_generator=answer_generator,
        )

        result = service.answer({"user_query": "Hello", "history": ["user: hi there"]})

        self.assertEqual(
            result.final_response,
            "Hello! How can I help you with COB Company's services or policies today?",
        )
        self.assertEqual(list(result.retrieved_context), [])
        self.assertEqual(embedding_generator.queries, [])
        self.assertEqual(searcher.calls, [])
        self.assertEqual(answer_generator.calls[0]["retrieved_context"], [])
        self.assertEqual(answer_generator.calls[0]["conversation_history"], ["user: hi there"])

    def test_filters_unrelated_retrieval_matches_before_answering(self) -> None:
        service = RetrievalKnowledgeBaseService(
            embedding_generator=StubEmbeddingGenerator([1.0]),
            searcher=StubVectorSearcher(
                [
                    VectorSearchMatch(
                        point_id="point-1",
                        record_id="faq_08750_chunk_0001",
                        score=0.95,
                        payload={
                            "faq_id": "faq_08750",
                            "category": "marketing",
                            "service_name": "Digital Marketing and Website Services",
                            "text": (
                                "Question: Do you support single-site and multi-location practices?\n"
                                "Answer: Yes. The mock dataset assumes support for single-site "
                                "and multi-location practices for Digital Marketing and Website "
                                "Services.\n"
                                "Service: Digital Marketing and Website Services"
                            ),
                        },
                    )
                ]
            ),
            answer_generator=StubAnswerGenerator("unused"),
        )

        result = service.answer({"user_query": "What does credentialing include?"})

        self.assertIn("could not find a grounded answer", result.final_response)
        self.assertEqual(list(result.retrieved_context), [])


if __name__ == "__main__":
    unittest.main()
