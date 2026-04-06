# KB Agent Walkthrough

This document explains how the current `kb_answer` path works in the project.

## Overview

The KB agent is the `kb_answer` branch of the graph.

It is a small RAG-style flow that:

1. receives the user query from graph state
2. checks recent conversation history
3. retrieves relevant FAQ context from Qdrant
4. builds a grounded prompt
5. sends that prompt to the configured LLM provider
6. returns the final answer back into graph state

If generation fails, it falls back to the best extractive FAQ answer.

## Where It Starts

The graph routes KB-style messages to:

- `app/graph/nodes/kb_answer.py`

That file is intentionally thin. It just calls the knowledge-base service.

More specifically now, the node calls a reusable graph agent from:

- `app/agents/kb_agent.py`

The real KB agent logic lives in:

- `app/services/knowledge_base.py`

## High-Level Flow

Inside `RetrievalKnowledgeBaseService`, the flow is:

1. Read `user_query` and `history` from `ChatState`
2. Detect whether the message is conversational like `hi` or `thanks`
3. If conversational:
   - skip retrieval
   - generate a short natural reply using the LLM path
4. If it is a KB question:
   - embed the query
   - search Qdrant
   - convert matches into retrieved context strings
   - send query + context + history to the LLM
5. If the LLM path fails:
   - fall back to the top FAQ answer directly

## Main Files

### Graph Node

- `app/graph/nodes/kb_answer.py`

This is the node that the graph executes.

### KB Service

- `app/services/knowledge_base.py`

This file owns:

- retrieval orchestration
- context shaping
- conversational-turn handling
- fallback behavior

### LLM Package

- `app/llm/prompts.py`
- `app/llm/factory.py`
- `app/llm/providers/openai.py`
- `app/llm/providers/gemini.py`

This package owns:

- the KB system prompt
- the KB user prompt builder
- provider selection
- provider-specific generation calls

## Prompt

The KB system prompt lives in:

- `app/llm/prompts.py`

It tells the model to:

- act as COB Company’s customer care AI assistant
- answer KB questions only from retrieved context
- say clearly when the KB is insufficient
- handle greetings naturally
- avoid inventing policies, pricing, timelines, or internal details

The KB user prompt builder also lives in:

- `app/llm/prompts.py`

It sends the model:

- recent conversation history
- the current customer question
- retrieved KB context
- an instruction to write the final customer answer

## Retrieval

For KB questions, the agent:

1. embeds the query using the configured embedding provider
2. searches Qdrant for the nearest FAQ matches
3. converts each match into a context block containing fields such as:
   - FAQ id
   - score
   - service
   - question
   - answer

That retrieved context is what grounds the final LLM answer.

## Memory

The KB agent uses session memory from graph state.

User and assistant messages are appended to `history` through:

- `app/graph/nodes/ingest_query.py`
- `app/graph/nodes/response.py`

The CLI preserves that state during a chat session in:

- `scripts/run_cli_chat.py`

This means follow-up questions can use prior turns as context.

Example:

```text
You: What does credentialing include?
You: What information is needed to start?
```

The second question can be interpreted using the first turn in history.

## Provider Selection

The provider factory lives in:

- `app/llm/factory.py`

It uses `KB_ANSWER_PROVIDER` from `.env`.

Current supported providers:

- `gemini`
- `openai`

## Fallback Behavior

If the LLM provider is not configured correctly or generation fails, the KB service falls back to the best extractive FAQ answer from the retrieved match.

This keeps the KB path usable even when live generation is unavailable.

## Current Weak Spot

The main weak spot is retrieval quality.

If retrieval returns the wrong FAQ, the LLM can still produce a grounded but wrong answer because it is grounded on the wrong context.

So the biggest quality drivers right now are:

- FAQ data quality
- embedding quality
- using the same embedding provider for ingestion and query time
- retrieval filtering and reranking

## Current Recommendation

For testing the KB agent:

1. ingest the high-quality FAQ set
2. use the same embedding provider for ingestion and chat
3. test direct KB questions first
4. then test follow-up questions and memory behavior

## Suggested Test Questions

```text
What does credentialing include?
What information is usually needed to start credentialing?
What does benefits verification involve?
What are common reasons claims get denied?
When does the chatbot escalate a conversation to a human?
```
