from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from vector_db.contracts import VectorDatabaseSetup
from vector_db.models import VectorCollectionSetupResult


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class QdrantSettings:
    collection_name: str
    embedding_dimension: int
    storage_path: Path
    distance: Distance
    prefer_grpc: bool = False
    url: str | None = None
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> "QdrantSettings":
        distance_name = os.getenv("QDRANT_DISTANCE", "cosine").strip().upper()
        try:
            distance = Distance[distance_name]
        except KeyError as exc:
            supported = ", ".join(item.name.lower() for item in Distance)
            raise ValueError(
                f"Unsupported QDRANT_DISTANCE '{distance_name.lower()}'. "
                f"Use one of: {supported}."
            ) from exc

        return cls(
            collection_name=os.getenv("QDRANT_COLLECTION", "customer_care_kb"),
            embedding_dimension=int(os.getenv("QDRANT_EMBEDDING_DIMENSION", "1536")),
            storage_path=Path(
                os.getenv("QDRANT_PATH", "vector_db/qdrant/data/local")
            ),
            distance=distance,
            prefer_grpc=_parse_bool(os.getenv("QDRANT_PREFER_GRPC")),
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )


class QdrantVectorDatabaseSetup(VectorDatabaseSetup):
    def __init__(self, settings: QdrantSettings) -> None:
        self._settings = settings

    @property
    def settings(self) -> QdrantSettings:
        return self._settings

    def create_client(self) -> QdrantClient:
        if self._settings.url:
            return QdrantClient(
                url=self._settings.url,
                api_key=self._settings.api_key,
                prefer_grpc=self._settings.prefer_grpc,
            )

        self._settings.storage_path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(self._settings.storage_path))

    def ensure_collection(self) -> VectorCollectionSetupResult:
        client = self.create_client()

        if not client.collection_exists(self._settings.collection_name):
            client.create_collection(
                collection_name=self._settings.collection_name,
                vectors_config=VectorParams(
                    size=self._settings.embedding_dimension,
                    distance=self._settings.distance,
                ),
            )
            created = True
        else:
            created = False

        return VectorCollectionSetupResult(
            collection_name=self._settings.collection_name,
            created=created,
            backend=self._settings.url or str(self._settings.storage_path),
            embedding_dimension=self._settings.embedding_dimension,
            distance=self._settings.distance.name.lower(),
        )
