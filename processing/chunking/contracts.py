from __future__ import annotations

from abc import ABC, abstractmethod

from processing.chunking.models import ChunkingInput, TextChunk


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, item: ChunkingInput) -> list[TextChunk]:
        raise NotImplementedError
