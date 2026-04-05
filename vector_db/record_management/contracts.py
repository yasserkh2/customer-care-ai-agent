from __future__ import annotations

from typing import Protocol

from vector_db.record_management.models import StoredVectorRecord


class VectorRecordReader(Protocol):
    def count_records(self) -> int:
        ...

    def list_records(
        self,
        limit: int = 10,
        with_vectors: bool = False,
    ) -> list[StoredVectorRecord]:
        ...
