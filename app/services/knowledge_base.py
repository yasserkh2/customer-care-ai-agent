from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.graph.state import ChatState
from app.llm import AnswerGenerator, KbAnswerGeneratorFactory, is_conversational_query
from app.services.models import KnowledgeBaseAnswer
from processing.vectorization import build_embedding_generator
from processing.vectorization.contracts import EmbeddingGenerator
from vector_db.contracts import VectorSearcher
from vector_db.models import VectorSearchMatch

if TYPE_CHECKING:
    from vector_db.qdrant import QdrantSettings

_FAQ_TEXT_PATTERN = re.compile(
    r"^Question:\s*(?P<question>.*?)\n"
    r"Answer:\s*(?P<answer>.*?)\n"
    r"Service:\s*(?P<service>.*)$",
    re.DOTALL,
)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "include",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "us",
    "what",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True, slots=True)
class FaqContextItem:
    faq_id: str
    score: float
    category: str
    question: str
    answer: str
    service: str
    raw_text: str
    vector_score: float
    lexical_overlap: int = 0

    def as_retrieved_context(self) -> str:
        lines = [f"FAQ: {self.faq_id}", f"Score: {self.score:.4f}"]
        if self.category:
            lines.append(f"Category: {self.category}")
        if self.service:
            lines.append(f"Service: {self.service}")
        if self.question:
            lines.append(f"Question: {self.question}")
        if self.answer:
            lines.append(f"Answer: {self.answer}")
        elif self.raw_text:
            lines.append(f"Text: {self.raw_text}")
        return "\n".join(lines)


class RetrievalKnowledgeBaseService:
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator | None = None,
        searcher: VectorSearcher | None = None,
        answer_generator: AnswerGenerator | None = None,
        retrieval_limit: int = 3,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError("retrieval_limit must be greater than zero.")

        self._embedding_generator = embedding_generator
        self._searcher = searcher
        self._answer_generator = answer_generator
        self._retrieval_limit = retrieval_limit
        self._settings: QdrantSettings | None = None

    def answer(self, state: ChatState) -> KnowledgeBaseAnswer:
        query = state.get("user_query", "").strip()
        if not query:
            return KnowledgeBaseAnswer(
                final_response=(
                    "Please share your question and I will look for the closest "
                    "knowledge-base answer."
                )
            )

        history = list(state.get("history", []))

        if is_conversational_query(query):
            return KnowledgeBaseAnswer(
                final_response=self._generate_conversational_or_fallback_answer(
                    user_query=query,
                    conversation_history=history,
                )
            )

        try:
            matches = self._retrieve(query)
        except Exception:
            return KnowledgeBaseAnswer(
                final_response=(
                    "I could not access the knowledge base just now. "
                    "Please try again after the retrieval setup is ready."
                )
            )

        if not matches:
            return KnowledgeBaseAnswer(
                final_response=(
                    "I could not find a grounded answer in the knowledge base yet. "
                    "Please rephrase your question or share a little more detail."
                )
            )

        context_items = self._build_ranked_context_items(query=query, matches=matches)
        if not context_items:
            return KnowledgeBaseAnswer(
                final_response=(
                    "I could not find a grounded answer in the knowledge base yet. "
                    "Please rephrase your question or share a little more detail."
                )
            )

        retrieved_context = [
            context_item.as_retrieved_context() for context_item in context_items
        ]
        final_response = self._generate_or_fallback_answer(
            user_query=query,
            context_items=context_items,
            retrieved_context=retrieved_context,
            conversation_history=history,
        )
        return KnowledgeBaseAnswer(
            final_response=final_response,
            retrieved_context=retrieved_context,
        )

    def _retrieve(self, query: str) -> list[VectorSearchMatch]:
        embedding_generator = self._get_embedding_generator()
        searcher = self._get_searcher()
        query_vector = embedding_generator.embed_query(query)
        return searcher.search(
            query_vector=query_vector,
            limit=self._retrieval_limit,
            with_vectors=False,
        )

    def _generate_or_fallback_answer(
        self,
        user_query: str,
        context_items: list[FaqContextItem],
        retrieved_context: list[str],
        conversation_history: list[str],
    ) -> str:
        try:
            generator = self._get_answer_generator()
        except Exception:
            generator = None

        if generator is None:
            return self._build_fallback_answer(context_items[0])

        try:
            generated_answer = generator.generate_answer(
                user_query=user_query,
                retrieved_context=retrieved_context,
                conversation_history=conversation_history,
            ).strip()
        except Exception:
            return self._build_fallback_answer(context_items[0])

        if not generated_answer:
            return self._build_fallback_answer(context_items[0])

        return generated_answer

    def _generate_conversational_or_fallback_answer(
        self,
        user_query: str,
        conversation_history: list[str],
    ) -> str:
        try:
            generator = self._get_answer_generator()
        except Exception:
            generator = None

        if generator is None:
            return self._build_conversational_fallback_answer(user_query)

        try:
            generated_answer = generator.generate_answer(
                user_query=user_query,
                retrieved_context=[],
                conversation_history=conversation_history,
            ).strip()
        except Exception:
            return self._build_conversational_fallback_answer(user_query)

        return generated_answer or self._build_conversational_fallback_answer(user_query)

    def _get_embedding_generator(self) -> EmbeddingGenerator:
        if self._embedding_generator is None:
            settings = self._get_settings()
            self._embedding_generator = build_embedding_generator(
                settings.embedding_dimension
            )
        return self._embedding_generator

    def _get_searcher(self) -> VectorSearcher:
        if self._searcher is None:
            from vector_db.qdrant import QdrantVectorSearcher

            self._searcher = QdrantVectorSearcher(settings=self._get_settings())
        return self._searcher

    def _get_answer_generator(self) -> AnswerGenerator | None:
        if self._answer_generator is None:
            self._answer_generator = KbAnswerGeneratorFactory().build()
        return self._answer_generator

    def _get_settings(self) -> QdrantSettings:
        if self._settings is None:
            from vector_db.qdrant import QdrantSettings

            self._settings = QdrantSettings.from_env()
        return self._settings

    def _build_context_item(self, match: VectorSearchMatch) -> FaqContextItem:
        payload_text = str(match.payload.get("text", "")).strip()
        parsed = _FAQ_TEXT_PATTERN.match(payload_text)
        if parsed is None:
            question = ""
            answer = payload_text
            service = str(match.payload.get("service_name", "")).strip()
        else:
            question = parsed.group("question").strip()
            answer = parsed.group("answer").strip()
            service = parsed.group("service").strip()

        faq_id = str(match.payload.get("faq_id", "")).strip() or match.record_id
        category = str(match.payload.get("category", "")).strip()
        return FaqContextItem(
            faq_id=faq_id,
            score=match.score,
            category=category,
            question=question,
            answer=answer,
            service=service,
            raw_text=payload_text,
            vector_score=match.score,
        )

    def _build_ranked_context_items(
        self,
        query: str,
        matches: list[VectorSearchMatch],
    ) -> list[FaqContextItem]:
        query_tokens = _normalize_tokens(query)
        context_items = [self._build_context_item(match) for match in matches]
        scored_items = [
            self._with_lexical_overlap(item=context_item, query_tokens=query_tokens)
            for context_item in context_items
        ]
        filtered_items = [
            item for item in scored_items if self._is_relevant_match(item, query_tokens)
        ]
        filtered_items.sort(
            key=lambda item: (item.lexical_overlap, item.vector_score),
            reverse=True,
        )
        return filtered_items

    def _with_lexical_overlap(
        self,
        item: FaqContextItem,
        query_tokens: set[str],
    ) -> FaqContextItem:
        candidate_tokens = _normalize_tokens(
            " ".join(
                part
                for part in [
                    item.question,
                    item.answer,
                    item.service,
                    item.category,
                ]
                if part
            )
        )
        return FaqContextItem(
            faq_id=item.faq_id,
            score=item.score,
            category=item.category,
            question=item.question,
            answer=item.answer,
            service=item.service,
            raw_text=item.raw_text,
            vector_score=item.vector_score,
            lexical_overlap=len(query_tokens & candidate_tokens),
        )

    def _is_relevant_match(
        self,
        item: FaqContextItem,
        query_tokens: set[str],
    ) -> bool:
        if not query_tokens:
            return True

        if item.lexical_overlap > 0:
            return True

        return item.vector_score >= 0.97

    def _build_fallback_answer(self, best_item: FaqContextItem) -> str:
        answer = (
            best_item.answer
            or best_item.raw_text
            or "I found a related FAQ entry, but its answer text was empty."
        )
        source_bits: list[str] = []
        if best_item.service:
            source_bits.append(f"Service: {best_item.service}")
        if best_item.faq_id:
            source_bits.append(f"Source: FAQ {best_item.faq_id}")
        if not source_bits:
            return answer
        return f"{answer}\n\n{' | '.join(source_bits)}"

    def _build_conversational_fallback_answer(self, user_query: str) -> str:
        normalized_query = user_query.strip().lower()
        if any(token in normalized_query for token in {"hello", "hi", "hey", "good morning", "good evening"}):
            return (
                "Hello! I can help with questions about COB Company's services, "
                "policies, and general information."
            )
        if "thank" in normalized_query:
            return "You're welcome. Let me know if you'd like help with anything else."
        return (
            "I can help with COB Company questions about services, policies, and "
            "general information."
        )


def _normalize_tokens(text: str) -> set[str]:
    tokens = {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token and token not in _STOPWORDS and len(token) > 2
    }
    return tokens
