from __future__ import annotations

from processing.chunking.models import TextChunk
from processing.vectorization.contracts import (
    EmbeddingGenerator,
    VectorizationStrategy,
)
from processing.vectorization.models import VectorizationResult
from vector_db.models import VectorRecord


class FaqVectorizationStrategy(VectorizationStrategy):
    def __init__(self, embedding_generator: EmbeddingGenerator) -> None:
        self._embedding_generator = embedding_generator

    def vectorize(self, chunks: list[TextChunk]) -> VectorizationResult:
        vector_records = [self._build_vector_record(chunk) for chunk in chunks]
        return VectorizationResult(
            records_processed=len(vector_records),
            vector_records=vector_records,
        )

    def _build_vector_record(self, chunk: TextChunk) -> VectorRecord:
        return VectorRecord(
            record_id=chunk.chunk_id,
            text=chunk.text,
            metadata=chunk.metadata,
            embedding=self._embedding_generator.embed_text(chunk.text),
        )
