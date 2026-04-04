from __future__ import annotations

from abc import ABC, abstractmethod

from processing.models import IngestionResult, IngestionSource


class IngestionPipeline(ABC):
    @abstractmethod
    def ingest(self, source: IngestionSource) -> IngestionResult:
        raise NotImplementedError
