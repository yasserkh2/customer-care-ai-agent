# FAQ Ingestion Metadata Plan

This note defines how FAQ records will be prepared before they are stored in the vector database.

## Source

Initial source:

- `cob_mock_kb_large/very_large_mixed_kb/faqs/faqs.jsonl`

Example record:

```json
{
  "faq_id": "faq_00001",
  "service_id": "svc_credentialing",
  "service_name": "Credentialing and Provider Maintenance",
  "question": "What does Credentialing and Provider Maintenance include for growing practices?",
  "answer": "Credentialing and Provider Maintenance includes support around credentialing, provider enrollment, and related operational workflows tailored to practice goals.",
  "category": "policy",
  "difficulty": "standard",
  "source": "synthetic_interview_dataset"
}
```

## Goal

Keep only semantically useful content in the embedded text and keep filtering or tracing fields in metadata.

## Embedded Text

The embedded text should contain:

- `question`
- `answer`
- `service_name`

Shape:

```text
Question: <question>
Answer: <answer>
Service: <service_name>
```

Example:

```text
Question: What does Credentialing and Provider Maintenance include for growing practices?
Answer: Credentialing and Provider Maintenance includes support around credentialing, provider enrollment, and related operational workflows tailored to practice goals.
Service: Credentialing and Provider Maintenance
```

## Metadata

The metadata should contain:

- `faq_id`
- `service_id`
- `service_name`
- `category`
- `difficulty`
- `source`
- `source_file`

These fields are useful for:

- filtering
- debugging
- source tracing
- later analytics

## Fields Not Needed In Embedded Text

Do not include these in the embedded text:

- `faq_id`
- `service_id`
- `difficulty`
- `source`

Reason:

- They add little semantic value to embeddings.
- They are more useful as metadata than retrieval text.

## Record Shape In Code

The FAQ ingestion pipeline should normalize each row into:

- `record_id`
- `text`
- `metadata`

Where:

- `record_id` = `faq_id`
- `text` = question + answer + service name
- `metadata` = the agreed FAQ metadata fields

## Current Implementation Direction

The FAQ ingestion pipeline lives in:

- `processing/ingestion_pipeline/faqs.py`

The next step after normalization is:

1. convert each normalized FAQ record into a vector-ready record
2. generate embeddings for the `text`
3. upsert the embeddings plus metadata into the vector database
