from __future__ import annotations

from vector_db.qdrant.setup import QdrantSettings, QdrantVectorDatabaseSetup
from vector_db.record_management.contracts import VectorRecordReader
from vector_db.record_management.models import StoredVectorRecord


class QdrantVectorRecordReader(VectorRecordReader):
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

    def count_records(self) -> int:
        result = self._client.count(
            collection_name=self.settings.collection_name,
            exact=True,
        )
        return result.count

    def list_records(
        self,
        limit: int = 10,
        with_vectors: bool = False,
    ) -> list[StoredVectorRecord]:
        records, _ = self._client.scroll(
            collection_name=self.settings.collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=with_vectors,
        )

        return [self._to_stored_record(record, with_vectors) for record in records]

    def _to_stored_record(
        self,
        record: object,
        with_vectors: bool,
    ) -> StoredVectorRecord:
        point_id = str(record.id)
        payload = dict(record.payload or {})
        record_id = str(payload.get("record_id", point_id))
        vector = None

        if with_vectors:
            vector_data = record.vector
            if isinstance(vector_data, list):
                vector = vector_data
            elif vector_data is not None:
                vector = list(vector_data)

        return StoredVectorRecord(
            point_id=point_id,
            record_id=record_id,
            payload=payload,
            vector=vector,
        )
