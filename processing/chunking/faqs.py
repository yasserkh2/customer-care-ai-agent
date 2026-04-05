from __future__ import annotations

from processing.chunking.contracts import ChunkingStrategy
from processing.chunking.models import ChunkingInput, TextChunk


class FaqChunkingStrategy(ChunkingStrategy):
    def chunk(self, item: ChunkingInput) -> list[TextChunk]:
        return [
            TextChunk(
                chunk_id=f"{item.record_id}_chunk_0001",
                text=item.text,
                metadata=item.metadata,
            )
        ]
