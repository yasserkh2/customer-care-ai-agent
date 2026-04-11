from __future__ import annotations

import atexit
import hashlib
import logging
import os
import shutil
import tempfile
from time import perf_counter
from dataclasses import replace
from pathlib import Path

from vector_db.contracts import VectorSearcher
from vector_db.models import VectorSearchMatch
from vector_db.qdrant.setup import QdrantSettings, QdrantVectorDatabaseSetup

logger = logging.getLogger("customer_care_ai.vector_db.qdrant.search")
_LOCKED_STORAGE_ERROR_FRAGMENT = (
    "already accessed by another instance of Qdrant client"
)
_MIRROR_ROOT = Path(tempfile.gettempdir()) / "customer_care_ai_qdrant_mirror"
_CREATED_MIRRORS: set[Path] = set()


def _cleanup_mirrors() -> None:
    for mirror_path in list(_CREATED_MIRRORS):
        try:
            shutil.rmtree(mirror_path, ignore_errors=True)
        except Exception:
            pass
        _CREATED_MIRRORS.discard(mirror_path)


atexit.register(_cleanup_mirrors)


class QdrantVectorSearcher(VectorSearcher):
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

        create_client_start = perf_counter()
        try:
            self._client = self._setup.create_client()
            create_client_ms = (perf_counter() - create_client_start) * 1000
            logger.info(
                "qdrant search client ready collection='%s' storage='%s' init_ms=%.1f",
                self._setup.settings.collection_name,
                self._setup.settings.storage_path,
                create_client_ms,
            )
        except RuntimeError as exc:
            # Embedded local Qdrant storage is single-writer/single-process.
            # When another process holds the lock, we mirror the store to a
            # temporary path and use that mirrored snapshot for read-only search.
            if self._setup.settings.url or not _is_locked_local_storage_error(exc):
                raise

            mirror_start = perf_counter()
            mirror_path = _create_storage_mirror(self._setup.settings.storage_path)
            mirror_ms = (perf_counter() - mirror_start) * 1000
            logger.warning(
                "qdrant local storage was locked at '%s'; "
                "using mirrored read-only snapshot at '%s' (mirror_copy_ms=%.1f)",
                self._setup.settings.storage_path,
                mirror_path,
                mirror_ms,
            )
            mirror_settings = replace(self._setup.settings, storage_path=mirror_path)
            self._setup = QdrantVectorDatabaseSetup(mirror_settings)
            mirrored_client_start = perf_counter()
            self._client = self._setup.create_client()
            mirrored_init_ms = (perf_counter() - mirrored_client_start) * 1000
            logger.info(
                "qdrant mirrored search client ready collection='%s' storage='%s' init_ms=%.1f",
                self._setup.settings.collection_name,
                self._setup.settings.storage_path,
                mirrored_init_ms,
            )

    @property
    def settings(self) -> QdrantSettings:
        return self._setup.settings

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        with_vectors: bool = False,
    ) -> list[VectorSearchMatch]:
        response = self._client.query_points(
            collection_name=self.settings.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=with_vectors,
        )

        return [
            self._to_search_match(point=point, with_vectors=with_vectors)
            for point in response.points
        ]

    def _to_search_match(
        self,
        point: object,
        with_vectors: bool,
    ) -> VectorSearchMatch:
        point_id = str(point.id)
        payload = dict(point.payload or {})
        record_id = str(payload.get("record_id", point_id))
        vector = None

        if with_vectors:
            vector_data = point.vector
            if isinstance(vector_data, list):
                vector = vector_data
            elif vector_data is not None:
                vector = list(vector_data)

        return VectorSearchMatch(
            point_id=point_id,
            record_id=record_id,
            score=float(point.score),
            payload=payload,
            vector=vector,
        )


def _is_locked_local_storage_error(exc: Exception) -> bool:
    return _LOCKED_STORAGE_ERROR_FRAGMENT.lower() in str(exc).lower()


def _create_storage_mirror(source_path: Path) -> Path:
    source = source_path.resolve()
    source_key = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:12]
    mirror_path = _MIRROR_ROOT / f"{source_key}_{os.getpid()}"

    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    if mirror_path.exists():
        shutil.rmtree(mirror_path, ignore_errors=True)

    shutil.copytree(source, mirror_path)
    _CREATED_MIRRORS.add(mirror_path)
    return mirror_path
