# Vector DB Architecture

This note explains where the vector database code should live in this repository and why the interface should be part of `vector_db/`, not `app/services/`.

## Short Answer

The code should be split like this:

- `app/services/` for application and business behavior
- `vector_db/` for vector-database abstractions and infrastructure
- `vector_db/qdrant/` for the Qdrant-specific implementation

That means:

- the interface belongs in `vector_db/contracts.py`
- Qdrant setup code belongs in `vector_db/qdrant/`
- `app/services` should use the abstraction, not define the infrastructure contract

## Why `app/services/` Is Not the Best Place

`app/services/` is the application service layer. In this repo, that layer is meant for business-facing behavior such as:

- knowledge-base answering
- intent handling
- response building
- orchestration of user-facing logic

A vector database is infrastructure. It is closer to:

- storage
- indexing
- retrieval plumbing
- external technology integration

If the vector DB contract lives in `app/services/`, the service layer starts owning infrastructure details that should stay lower in the architecture.

## Why `vector_db/` Is the Better Place

`vector_db/` is the natural home for all vector storage concerns.

That includes:

- common interfaces
- vector DB result models
- generic retrieval abstractions
- vendor-specific adapters
- local runtime assets such as Docker setup and storage directories

This gives a cleaner separation:

- `app/services` describes what the application needs
- `vector_db` describes how vector storage is provided

## Recommended Structure

A clean OOP-oriented layout is:

```text
app/
  services/
    contracts.py
    models.py
    responses.py
    ...

vector_db/
  contracts.py
  models.py
  ARCHITECTURE.md
  qdrant/
    setup.py
    docker-compose.yml
    README.md
    DECISION.md
    SETUP_SPECS.md
    data/
```

## Responsibility Split

### `app/services`

This layer should contain business-facing contracts such as:

- `KnowledgeBaseService`
- `ActionRequestService`
- `EscalationService`

These services may depend on vector search, but they should not define vector DB technology contracts themselves.

### `vector_db/contracts.py`

This file should contain generic infrastructure contracts such as:

- `VectorDatabaseSetup`
- future `VectorSearchRepository`
- future `VectorDocumentStore`

These contracts should be implementation-agnostic so the app can use them without caring whether the concrete implementation is Qdrant, Pinecone, Weaviate, or something else.

### `vector_db/qdrant/`

This directory should contain Qdrant-specific code such as:

- settings
- client creation
- collection setup
- Qdrant repositories
- Docker runtime files

This keeps vendor-specific logic isolated and makes the codebase easier to evolve.

## OOP Reasoning

From an OOP perspective, the goal is dependency inversion:

- higher-level application services should depend on abstractions
- lower-level vendor adapters should implement those abstractions

If `app/services` defines the vector DB interface, the design becomes muddier because the service layer starts owning infrastructure contracts. It is cleaner to place the abstraction in the infrastructure domain that it represents.

So the dependency direction should look like this:

```text
app/services -> vector_db/contracts -> vector_db/qdrant
```

Not this:

```text
app/services -> app/services/vector interface -> qdrant implementation
```

The first version keeps boundaries clearer.

## Practical Rule

Use this rule going forward:

- if the code expresses business behavior, keep it in `app/services`
- if the code expresses vector storage behavior, keep it in `vector_db`
- if the code is vendor-specific, keep it in `vector_db/<vendor>`

## Final Recommendation

For this repo:

- move `VectorDatabaseSetup` out of `app/services/contracts.py`
- move `VectorCollectionSetupResult` out of `app/services/models.py`
- place both in `vector_db/`
- keep Qdrant setup code in `vector_db/qdrant/setup.py`

This gives a cleaner architecture, better separation of concerns, and a more OOP-oriented design.
