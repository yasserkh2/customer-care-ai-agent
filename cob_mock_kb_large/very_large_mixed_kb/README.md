# COB Very Large Mixed KB

This dataset is the large mixed-format knowledge base for the customer-care chatbot task. It is meant to support three main implementation areas:

- grounded knowledge-base answers
- action flows such as consultation booking or contact updates
- human escalation and case-awareness logic

The folder includes both retrieval-friendly content and operational mock data so you can build a realistic `kb_answer` path first, then expand into `action_request` and `human_escalation`.

## What This Dataset Is For

Use this folder when you need:

- broad knowledge coverage across documents, FAQs, and structured company data
- enough volume to simulate real retrieval instead of hardcoded answers
- sample operational records for appointments and support cases
- service metadata you can use for routing, answer grounding, and entity normalization

This is especially useful for the project’s current next step:

- replacing the placeholder `kb_answer` behavior with retrieval over a realistic organization knowledge base

## Scale

- Markdown documents: 1200
- FAQ entries: 10000
- Case note rows: 4000
- Appointment rows: 20000
- KPI rows: 2000

## Folder Map

- `documents/`
  Contains long-form service playbooks in Markdown. These are the best source when the user asks broad or descriptive questions and you want richer grounded context.
- `faqs/`
  Contains short question-answer pairs in JSONL and CSV. These are the best source for direct customer questions that should return a concise answer quickly.
- `structured/`
  Contains organization metadata, service definitions, product references, document index metadata, and KPI-style records. This is the best source for filtering, normalization, linking records together, and supporting deterministic answers.
- `case_notes/`
  Contains mock historical support cases. This is useful for escalation-related features, case lookups, and status-aware responses.
- `appointments/`
  Contains mock consultation/booking records. This is useful for booking, rescheduling, cancellation, and confirmation-style workflows.

## File-By-File Usage Guide

### `structured/structured_data.json`

Use this as the top-level organization reference.

It contains:

- company profile information
- general business facts
- product definitions
- service relationships
- workflow/task metadata in a single structured document

Use it when:

- the user asks general company questions
- you need canonical service or product names
- you want to enrich a retrieved answer with organization-level facts
- you want to keep `kb_answer` grounded without searching the full document set first

Good examples:

- "What kind of company is COB Solution?"
- "What services do you offer?"
- "Do you support healthcare practices?"

### `structured/services.csv`

Use this as the canonical service catalog.

It contains:

- `id`
- `name`
- `department`
- `summary`

Use it when:

- you want to normalize a user query to a known service
- you need a compact service description
- you want to map free-text intent to a `service_id`
- you need a quick lookup before searching FAQs or documents

This file is a good first pass in `kb_answer` because it is small, structured, and easy to filter.

### `structured/service_kpis.csv`

Use this only for metric or performance-style questions.

It contains:

- response time metrics
- resolution metrics
- CSAT scores
- escalation-rate percentages
- monthly records by `service_id`

Use it when:

- the user asks about service performance
- you want reporting-oriented answers
- you need structured evidence for analytics questions

Good examples:

- "What is the average response time for customer care?"
- "How do billing denials KPIs look in 2026-03?"

This should usually not be your primary source for normal FAQ answers.

### `structured/documents_index.json`

Use this as the metadata layer for the Markdown documents.

It contains:

- `doc_id`
- `service_id`
- `service_name`
- `title`
- `file_path`
- `region`
- `practice_type`
- `phase`
- `tags`

Use it when:

- you want to filter candidate documents before opening them
- you need region-aware or specialty-aware retrieval
- you want to avoid scanning all 1200 Markdown files every time

Recommended pattern:

1. Match the query to `service_id`, tags, region, practice type, or phase using `documents_index.json`
2. Open the top matching Markdown files from `documents/`
3. Extract concise grounded context for the final response

### `documents/*.md`

Use these as the richest retrieval source for detailed grounded answers.

Typical content includes:

- overview
- practice context
- common customer questions
- response guidelines
- data collection checklist
- escalation notes
- keywords

Use them when:

- the user asks "how", "what is included", "what happens next", or similar descriptive questions
- you need more nuance than a one-line FAQ
- you want to support multi-step grounded responses

These files are ideal for `kb_answer` after you shortlist candidates through `documents_index.json`.

### `faqs/faqs.jsonl`

Use this as the primary fast-answer source for `kb_answer`.

It contains one JSON object per line with fields such as:

- `faq_id`
- `service_id`
- `service_name`
- `question`
- `answer`
- `category`
- `difficulty`

Use it when:

- the user asks a direct support-style question
- you want a concise answer with minimal processing
- you want easier programmatic loading than CSV

This is likely the best first real data source to connect into the `KnowledgeBaseService`.

### `faqs/faqs.csv`

This is the same FAQ content in CSV format.

Use it when:

- you want spreadsheet-style inspection
- you prefer CSV tooling
- you are doing quick manual analysis outside the app

For application code, `faqs.jsonl` is usually the better source because it is easier to stream and parse reliably.

### `case_notes/case_notes.jsonl`

Use this for escalation-aware and history-aware features, not for public FAQ answers.

It contains fields such as:

- `case_id`
- `service_id`
- `practice_name`
- `region`
- `practice_type`
- `priority`
- `status`
- `summary`
- `escalated`
- `channel`

Use it when:

- building `human_escalation`
- checking whether similar cases are already open
- creating realistic handoff context for a human team
- supporting status or case-history workflows

This dataset is operational, not canonical knowledge. Avoid using it as the main answer source for general company questions.

### `appointments/appointments.jsonl`

Use this as the main operational dataset for scheduling-related flows.

It contains fields such as:

- `appointment_id`
- `service_id`
- `practice_name`
- `contact_name`
- `email`
- `phone`
- `date`
- `time`
- `status`
- `booking_channel`
- `reference_code`

Use it when:

- building consultation booking
- implementing reschedule or cancellation logic
- checking if a user already has an appointment
- generating realistic confirmation responses

This is most relevant to `action_request`, not `kb_answer`.

### `appointments/appointments.csv`

This is the appointment data in CSV format.

Use it when:

- you want spreadsheet-style inspection
- you need simple CSV tooling
- you are validating the generated data manually

For application code, `appointments.jsonl` is usually the better source.

### `dataset_manifest.json`

Use this as a quick machine-readable summary of the dataset.

It contains:

- dataset name
- version
- creation date
- record counts
- format summary

Use it when:

- validating dataset presence
- showing metadata in tooling
- writing scripts that need to know expected file counts

## Which Files Should Power Each Node

### `kb_answer`

Primary sources:

- `faqs/faqs.jsonl`
- `structured/services.csv`
- `structured/structured_data.json`
- `structured/documents_index.json`
- `documents/*.md`

Suggested priority:

1. Try exact or close FAQ match
2. Normalize the service using `services.csv`
3. Use `structured_data.json` for company-level facts
4. Use `documents_index.json` to shortlist documents
5. Read one or more Markdown files for richer grounding

### `action_request`

Primary sources:

- `appointments/appointments.jsonl`
- `structured/services.csv`
- `documents/*.md`

Suggested use:

- identify the requested service from `services.csv`
- collect missing appointment fields
- create or simulate a booking using the appointments dataset
- optionally use service playbooks to know which information to collect

### `human_escalation`

Primary sources:

- `case_notes/case_notes.jsonl`
- `documents/*.md`
- `structured/services.csv`

Suggested use:

- detect whether the issue is sensitive or unresolved
- attach service context
- include useful case-style summary details for handoff
- use document escalation notes to shape policy

## Practical Development Order

If you are implementing this repo step by step, a good order is:

1. Start with `faqs/faqs.jsonl` for the first real `KnowledgeBaseService`
2. Add `structured/services.csv` so service matching becomes more reliable
3. Add `structured/structured_data.json` for general company facts
4. Add `documents_index.json` plus `documents/*.md` for richer retrieval
5. Add `appointments/appointments.jsonl` when you move into booking workflows
6. Add `case_notes/case_notes.jsonl` when you improve escalation behavior

## Recommended Retrieval Strategy For This Task

For the current project, a practical `kb_answer` strategy is:

1. Normalize the user query
2. Detect likely service names or keywords using `services.csv`
3. Search FAQ questions and answers for the fastest grounded response
4. If confidence is low, search `documents_index.json` for matching metadata
5. Open the top relevant Markdown documents
6. Return a concise answer plus optional next-step guidance

This gives you a simple path first and leaves room to evolve later into stronger retrieval or full RAG.

## Notes

- All records are synthetic and intended for interview/demo use.
- Appointment dates begin on 2026-04-06 and extend forward for large-volume simulation.
- Prefer JSONL files for app code and CSV files for quick inspection.
- Prefer `documents_index.json` before scanning all Markdown documents directly.
