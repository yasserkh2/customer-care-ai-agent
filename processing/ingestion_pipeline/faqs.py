from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from processing.chunking.models import ChunkingInput
from processing.ingestion_pipeline.contracts import IngestionPipeline
from processing.ingestion_pipeline.models import IngestionResult, IngestionSource


@dataclass(frozen=True, slots=True)
class ProcessedFaqRecord:
    faq_id: str
    service_id: str
    service_name: str
    question: str
    answer: str
    category: str
    difficulty: str
    source: str
    source_file: str

    @property
    def record_id(self) -> str:
        return self.faq_id

    @property
    def text(self) -> str:
        return (
            f"Question: {self.question}\n"
            f"Answer: {self.answer}\n"
            f"Service: {self.service_name}"
        )

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "faq_id": self.faq_id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "category": self.category,
            "difficulty": self.difficulty,
            "source": self.source,
            "source_file": self.source_file,
        }

    def as_chunking_input(self) -> ChunkingInput:
        return ChunkingInput(
            record_id=self.record_id,
            text=self.text,
            metadata=self.metadata,
        )


class FaqJsonlIngestionPipeline(IngestionPipeline):
    def __init__(self) -> None:
        self._processed_records: list[ProcessedFaqRecord] = []

    @property
    def processed_records(self) -> list[ProcessedFaqRecord]:
        return list(self._processed_records)

    def ingest(self, source: IngestionSource) -> IngestionResult:
        source_path = Path(source.file_path)
        records: list[ProcessedFaqRecord] = []

        with source_path.open("r", encoding="utf-8") as file_obj:
            for line_number, raw_line in enumerate(file_obj, start=1):
                normalized_line = raw_line.strip()
                if not normalized_line:
                    continue

                payload = json.loads(normalized_line)
                records.append(
                    self._build_record(
                        payload=payload,
                        source_file=source_path.name,
                        line_number=line_number,
                    )
                )

        self._processed_records = records
        return IngestionResult(
            source_name=source.source_name,
            file_path=source.file_path,
            content_type=source.content_type,
            records_processed=len(records),
            points_upserted=0,
        )

    def _build_record(
        self,
        payload: dict[str, object],
        source_file: str,
        line_number: int,
    ) -> ProcessedFaqRecord:
        required_fields = (
            "faq_id",
            "service_id",
            "service_name",
            "question",
            "answer",
            "category",
            "difficulty",
            "source",
        )

        missing_fields = [
            field_name
            for field_name in required_fields
            if not isinstance(payload.get(field_name), str) or not payload[field_name]
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(
                f"FAQ record on line {line_number} is missing required fields: {missing}"
            )

        return ProcessedFaqRecord(
            faq_id=str(payload["faq_id"]),
            service_id=str(payload["service_id"]),
            service_name=str(payload["service_name"]),
            question=str(payload["question"]),
            answer=str(payload["answer"]),
            category=str(payload["category"]),
            difficulty=str(payload["difficulty"]),
            source=str(payload["source"]),
            source_file=source_file,
        )
