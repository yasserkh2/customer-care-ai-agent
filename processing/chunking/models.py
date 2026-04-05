from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ChunkingInput:
    record_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TextChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
