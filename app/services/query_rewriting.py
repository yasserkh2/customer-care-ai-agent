from __future__ import annotations

from time import perf_counter

from app.llm.contracts import RetrievalQueryGenerator
from app.llm.retrieval_query_factory import RetrievalQueryGeneratorFactory
from app.observability import get_logger, truncate_text

logger = get_logger("services.query_rewriting")


class LlmRetrievalQueryRewriter:
    def __init__(
        self,
        generator: RetrievalQueryGenerator | None = None,
    ) -> None:
        self._generator = generator

    def rewrite(self, query: str, history: list[str]) -> str:
        normalized_query = query.strip()
        if not normalized_query:
            return normalized_query

        generator = self._get_generator()
        if generator is None:
            raise RuntimeError("LLM retrieval query generator is unavailable.")

        rewrite_start = perf_counter()
        rewritten = generator.generate_query(
            user_query=normalized_query,
            conversation_history=history,
        ).strip()
        rewrite_ms = (perf_counter() - rewrite_start) * 1000

        if not rewritten:
            raise RuntimeError("LLM retrieval query generator returned an empty query.")

        logger.info(
            "llm retrieval query generated: original='%s' rewritten='%s' latency_ms=%.1f",
            truncate_text(normalized_query, 120),
            truncate_text(rewritten, 120),
            rewrite_ms,
        )
        return rewritten

    def _get_generator(self) -> RetrievalQueryGenerator | None:
        if self._generator is not None:
            return self._generator
        try:
            self._generator = RetrievalQueryGeneratorFactory().build()
        except Exception as exc:
            logger.warning("retrieval query generator unavailable: %s", exc)
            self._generator = None
        return self._generator
