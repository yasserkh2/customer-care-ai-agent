# Dataset and Task Relation

This document explains how `cob_mock_kb_large/very_large_mixed_kb` relates to the requirements in `Customer Care AI Chatbot Agent Development Task-v2 (1) (1).md`.

## Short Answer

The dataset fully supports the task and is larger than the minimum data scope required by the brief.

It gives you enough data to implement:

- knowledge-base question answering
- action-oriented flows such as appointment booking
- human escalation support
- future RAG or hybrid retrieval

It is more complex than the minimum task because it contains high-volume mixed-format data, not just a small FAQ list or a few documents.

## Task Requirements and Dataset Mapping

### 1. Knowledge-Base Inquiry Answering

The task requires the chatbot to:

- answer questions about products, services, policies, and company information
- retrieve relevant information from a provided knowledge base
- provide concise and accurate answers
- support phrasing variation
- leave room for future RAG

Dataset files that support this:

- `faqs/faqs.jsonl`
- `faqs/faqs.csv`
- `documents/*.md`
- `structured/structured_data.json`
- `structured/services.csv`
- `structured/documents_index.json`

How they help:

- `faqs/faqs.jsonl` is the strongest starting point for concise KB answers
- `documents/*.md` provide richer long-form grounding for more detailed responses
- `structured/structured_data.json` provides company facts, products, and service relationships
- `structured/services.csv` helps normalize service names and user wording
- `structured/documents_index.json` helps filter and retrieve relevant documents efficiently

Conclusion:

The dataset clearly satisfies the KB-answering part of the task.

### 2. Action-Oriented Dialog Flows

The task requires the chatbot to:

- detect appointment or action intent
- gather required information
- maintain context
- confirm details
- simulate or integrate an execution step

Dataset files that support this:

- `appointments/appointments.jsonl`
- `appointments/appointments.csv`
- `structured/services.csv`
- `documents/*.md`

How they help:

- `appointments/appointments.jsonl` gives realistic booking-style records for mock scheduling flows
- `appointments/appointments.csv` is useful for manual inspection and validation
- `structured/services.csv` helps map user requests to known services
- `documents/*.md` often include collection checklists and next-step guidance that can inform slot-filling logic

Conclusion:

The dataset supports the action-flow part of the task, especially for mock booking and confirmation workflows.

### 3. Intent Classification and Human Escalation

The task requires the chatbot to:

- classify KB queries, action requests, and escalation needs
- escalate complex, sensitive, or unsupported issues
- support frustration-based escalation

Dataset files that support this:

- `case_notes/case_notes.jsonl`
- `documents/*.md`
- `structured/services.csv`
- `structured/structured_data.json`

How they help:

- `case_notes/case_notes.jsonl` provides realistic support-case style data for handoff context
- `documents/*.md` include escalation notes and response guidance
- `structured/services.csv` helps attach service context to escalations
- `structured/structured_data.json` helps define company-level support scope and supported workflows

Conclusion:

The dataset supports escalation logic, especially once the app moves beyond the current placeholder handoff behavior.

## Which Dataset Parts Match Which Node

### `kb_answer`

Best files:

- `faqs/faqs.jsonl`
- `structured/services.csv`
- `structured/structured_data.json`
- `structured/documents_index.json`
- `documents/*.md`

Role:

- retrieve grounded answers for service, company, and policy questions

### `action_request`

Best files:

- `appointments/appointments.jsonl`
- `structured/services.csv`
- `documents/*.md`

Role:

- identify requested service
- collect required booking fields
- simulate or validate appointment actions

### `human_escalation`

Best files:

- `case_notes/case_notes.jsonl`
- `documents/*.md`
- `structured/services.csv`

Role:

- create better escalation policies
- attach operational context to a handoff
- support sensitive or unresolved issue routing

## Is the Dataset Simpler or More Complex Than the Task?

### In data volume

It is more complex than the minimum brief requires.

Examples:

- 1200 Markdown documents
- 10000 FAQ items
- 20000 appointment rows
- 4000 case-note rows
- 2000 KPI rows

The task only requires a usable knowledge base and support for guided workflows. This dataset gives much more volume than the minimum needed to prove that.

### In implementation scope

The task is still broader than the dataset alone.

The dataset gives the content and records, but the project still needs application logic such as:

- retrieval and ranking
- answer generation
- intent classification
- entity extraction
- slot filling
- confirmation logic
- simulated execution
- escalation policy

So:

- the dataset is richer than the minimum data requirement
- the full task is larger than just having the dataset

## What Is Extra in the Dataset?

Some parts go beyond the strict minimum task:

- `structured/service_kpis.csv`
- large-scale case and appointment records
- metadata layers such as `documents_index.json`

These are useful for:

- analytics questions
- future filtering and reranking
- scaling retrieval beyond a toy demo

They are not required for the first version of the chatbot, but they make the dataset more realistic and extensible.

## Recommended Usage Strategy

If the goal is to meet the task efficiently, use the dataset in phases.

### Phase 1: First real `kb_answer`

Use:

- `faqs/faqs.jsonl`
- `structured/services.csv`

Goal:

- replace the placeholder KB response with real retrieval

### Phase 2: Better grounding

Use:

- `structured/structured_data.json`
- `structured/documents_index.json`
- `documents/*.md`

Goal:

- answer broader company questions and improve retrieval quality

### Phase 3: Action workflows

Use:

- `appointments/appointments.jsonl`

Goal:

- support booking, rescheduling, or mock execution flows

### Phase 4: Escalation improvements

Use:

- `case_notes/case_notes.jsonl`

Goal:

- support richer escalation context and smarter handoff behavior

## Final Conclusion

`cob_mock_kb_large/very_large_mixed_kb` is a strong fit for `Customer Care AI Chatbot Agent Development Task-v2 (1) (1).md`.

It does not fall short of the brief. Instead, it provides more data variety and scale than the minimum requirement, while still being organized enough to implement the task incrementally.

For the current project stage, the best starting subset is:

- `faqs/faqs.jsonl`
- `structured/services.csv`
- `structured/structured_data.json`

That subset is enough to begin real work on `kb_answer` without taking on the full complexity of the entire dataset at once.
