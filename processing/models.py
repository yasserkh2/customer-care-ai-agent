from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngestionSource:
    source_name: str
    file_path: str
    content_type: str


@dataclass(frozen=True, slots=True)
class IngestionResult:
    source_name: str
    file_path: str
    content_type: str
    records_processed: int
    points_upserted: int
