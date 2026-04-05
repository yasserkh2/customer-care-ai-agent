High-quality FAQ test set for retrieval evaluation.

Purpose:
- reduce repetitive synthetic wording
- make service boundaries clearer
- provide more realistic KB-style questions and answers
- improve retrieval quality for early RAG testing

File:
- `high_quality_faqs.jsonl`

Suggested ingestion command:

```bash
FAQS_JSONL_PATH=cob_mock_kb_large/high_quality_faqs/high_quality_faqs.jsonl .venv/bin/python scripts/run_faq_processing_pipeline.py
```

Recommended for isolated testing:

```bash
FAQS_JSONL_PATH=cob_mock_kb_large/high_quality_faqs/high_quality_faqs.jsonl QDRANT_PATH=vector_db/qdrant/data/high_quality_faqs .venv/bin/python scripts/run_faq_processing_pipeline.py
```
