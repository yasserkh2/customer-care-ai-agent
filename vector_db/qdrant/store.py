from __future__ import annotations

from collections.abc import Iterable
import uuid

from qdrant_client.models import PointStruct

from vector_db.contracts import VectorStore
from vector_db.models import VectorRecord, VectorUpsertResult
from vector_db.qdrant.setup import QdrantSettings, QdrantVectorDatabaseSetup


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        settings: QdrantSettings | None = None,
        setup: QdrantVectorDatabaseSetup | None = None,
    ) -> None:
        if setup is None and settings is None:
            raise ValueError("Provide either Qdrant settings or a setup instance.")

        if setup is not None:
            self._setup = setup
        else:
            self._setup = QdrantVectorDatabaseSetup(settings)
        self._client = self._setup.create_client()

    @property
    def settings(self) -> QdrantSettings:
        return self._setup.settings

    def upsert_records(self, records: Iterable[VectorRecord]) -> VectorUpsertResult:
        record_list = list(records)
        if not record_list:
            return VectorUpsertResult(
                collection_name=self.settings.collection_name,
                points_upserted=0,
            )

        self._client.upsert(
            collection_name=self.settings.collection_name,
            points=[self._build_point(record) for record in record_list],
            wait=True,
        )

        return VectorUpsertResult(
            collection_name=self.settings.collection_name,
            points_upserted=len(record_list),
        )

    def _build_point(self, record: VectorRecord) -> PointStruct:
        payload = dict(record.metadata)
        payload["record_id"] = record.record_id
        payload["text"] = record.text

        return PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, record.record_id)),
            vector=record.embedding,
            payload=payload,
        )
