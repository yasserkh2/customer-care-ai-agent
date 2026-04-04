from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from vector_db.models import (
    VectorCollectionSetupResult,
    VectorRecord,
    VectorUpsertResult,
)


class VectorDatabaseSetup(Protocol):
    def ensure_collection(self) -> VectorCollectionSetupResult:
        ...


class VectorStore(Protocol):
    def upsert_records(self, records: Iterable[VectorRecord]) -> VectorUpsertResult:
        ...
