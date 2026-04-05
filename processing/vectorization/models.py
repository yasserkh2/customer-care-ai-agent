from __future__ import annotations

from dataclasses import dataclass

from vector_db.models import VectorRecord


@dataclass(frozen=True, slots=True)
class VectorizationResult:
    records_processed: int
    vector_records: list[VectorRecord]
