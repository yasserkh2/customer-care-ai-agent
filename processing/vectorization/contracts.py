from __future__ import annotations

from abc import ABC, abstractmethod

from processing.chunking.models import TextChunk
from processing.vectorization.models import VectorizationResult


class EmbeddingGenerator(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError


class VectorizationStrategy(ABC):
    @abstractmethod
    def vectorize(self, chunks: list[TextChunk]) -> VectorizationResult:
        raise NotImplementedError
