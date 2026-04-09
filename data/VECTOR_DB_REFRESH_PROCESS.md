# Vector DB Refresh Process

## Purpose
This file documents the current process for replacing old vector embeddings with new embeddings built from:

- `data/documents`
- `data/faqs`

The chatbot currently reads from two local Qdrant collections:

- FAQ collection: `customer_care_kb`
- Document collection: `customer_care_documents_kb`

## Important Notes
- Use the project virtualenv: `.venv/bin/python`
- Run FAQ and document rebuilds one at a time
- Local Qdrant storage does not support concurrent writers
- The embedding provider needs network access

## 1. Delete Existing Collections
Use this script to remove the old local collections before rebuilding:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from app.config import load_runtime_config

load_runtime_config(config_path=Path('config.yml'), env_path=Path('.env'))

from vector_db.qdrant import QdrantSettings, QdrantVectorDatabaseSetup

for env_key, default in [
    ('QDRANT_COLLECTION', 'customer_care_kb'),
    ('QDRANT_DOCUMENT_COLLECTION', 'customer_care_documents_kb'),
]:
    settings = QdrantSettings.from_env(
        collection_env_key=env_key,
        collection_default=default,
    )
    setup = QdrantVectorDatabaseSetup(settings)
    client = setup.create_client()

    if client.collection_exists(settings.collection_name):
        client.delete_collection(settings.collection_name)
        print(f"deleted {settings.collection_name}")
    else:
        print(f"missing {settings.collection_name}")
PY
```

## 2. Rebuild Document Embeddings
Run the document pipeline against the new manifest:

```bash
DOCUMENTS_MANIFEST_PATH='data/documents/documents_manifest.json' \
.venv/bin/python scripts/run_document_processing_pipeline.py
```

This creates fresh vectors in:
- `customer_care_documents_kb`

## 3. Rebuild FAQ Embeddings
Run the FAQ pipeline against the new JSONL:

```bash
FAQS_JSONL_PATH='data/faqs/high_quality_faqs.jsonl' \
.venv/bin/python scripts/run_faq_processing_pipeline.py
```

This creates fresh vectors in:
- `customer_care_kb`

## 4. Verify Final Counts
Use this script to confirm the new vector counts:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from app.config import load_runtime_config

load_runtime_config(config_path=Path('config.yml'), env_path=Path('.env'))

from vector_db.qdrant import QdrantSettings, QdrantVectorDatabaseSetup
from vector_db.record_management import QdrantVectorRecordReader

for env_key, default in [
    ('QDRANT_COLLECTION', 'customer_care_kb'),
    ('QDRANT_DOCUMENT_COLLECTION', 'customer_care_documents_kb'),
]:
    settings = QdrantSettings.from_env(
        collection_env_key=env_key,
        collection_default=default,
    )
    reader = QdrantVectorRecordReader(
        setup=QdrantVectorDatabaseSetup(settings)
    )
    print(f"{settings.collection_name}: {reader.count_records()} points")
PY
```

## Expected Current Result
With the current `data/` dataset, the expected counts are:

- `customer_care_kb`: `10` points
- `customer_care_documents_kb`: `54` points

## Current Data Sources
- Documents: [documents_manifest.json](/media/yasser/New Volume1/yasser/New_journey/customer-care-ai-agent/data/documents/documents_manifest.json)
- FAQs: [high_quality_faqs.jsonl](/media/yasser/New Volume1/yasser/New_journey/customer-care-ai-agent/data/faqs/high_quality_faqs.jsonl)

## Optional Environment Overrides
If needed, these are the key runtime overrides:

```bash
DOCUMENTS_MANIFEST_PATH='data/documents/documents_manifest.json'
FAQS_JSONL_PATH='data/faqs/high_quality_faqs.jsonl'
```

## Summary
The current refresh flow is:

1. Delete old Qdrant collections
2. Rebuild document vectors from `data/documents`
3. Rebuild FAQ vectors from `data/faqs`
4. Verify the final stored point counts
