from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from processing.chunking import FaqChunkingStrategy
from processing.ingestion_pipeline import FaqJsonlIngestionPipeline, IngestionSource
from processing.vectorization import (
    DeterministicEmbeddingGenerator,
    FaqVectorizationStrategy,
)


def _build_source() -> IngestionSource:
    return IngestionSource(
        source_name="faq_jsonl",
        file_path=os.getenv(
            "FAQS_JSONL_PATH",
            "cob_mock_kb_large/very_large_mixed_kb/faqs/faqs.jsonl",
        ),
        content_type="application/jsonl",
    )


def _parse_limit() -> int | None:
    raw_limit = os.getenv("FAQ_PIPELINE_LIMIT", "").strip()
    if not raw_limit:
        return None

    limit = int(raw_limit)
    if limit <= 0:
        raise ValueError("FAQ_PIPELINE_LIMIT must be greater than zero.")
    return limit


def main() -> None:
    source = _build_source()
    limit = _parse_limit()

    ingestion_pipeline = FaqJsonlIngestionPipeline()
    chunking_strategy = FaqChunkingStrategy()
    vectorization_strategy = FaqVectorizationStrategy(
        DeterministicEmbeddingGenerator()
    )

    ingestion_result = ingestion_pipeline.ingest(source)
    processed_records = ingestion_pipeline.processed_records
    if limit is not None:
        processed_records = processed_records[:limit]

    chunks = []
    for record in processed_records:
        chunks.extend(chunking_strategy.chunk(record.as_chunking_input()))

    vectorization_result = vectorization_strategy.vectorize(chunks)

    print("FAQ processing pipeline complete.")
    print(f"Source file: {source.file_path}")
    print(f"Records ingested: {ingestion_result.records_processed}")
    print(f"Records selected: {len(processed_records)}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Vector records created: {vectorization_result.records_processed}")

    if vectorization_result.vector_records:
        sample_record = vectorization_result.vector_records[0]
        print("\nSample vector record:")
        print(f"Record ID: {sample_record.record_id}")
        print(f"Text preview: {sample_record.text[:160]}")
        print(f"Embedding dimension: {len(sample_record.embedding)}")
        print(
            "Metadata: "
            + json.dumps(sample_record.metadata, indent=2, sort_keys=True)
        )


if __name__ == "__main__":
    main()
