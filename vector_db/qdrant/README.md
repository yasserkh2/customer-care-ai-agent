# Qdrant Standalone Setup

This directory contains the Qdrant-specific setup for the project.

Contents:

- `docker-compose.yml`
- `DECISION.md`
- `SETUP_SPECS.md`
- local data paths under `data/`

The repo still keeps application integration code in:

- `vector_db/qdrant/setup.py`
- `scripts/setup_qdrant.py`

But the vector database assets themselves now live in this standalone directory.

## Directory Layout

- `vector_db/qdrant/docker-compose.yml`
- `vector_db/contracts.py`
- `vector_db/models.py`
- `vector_db/ARCHITECTURE.md`
- `vector_db/qdrant/data/local/`
- `vector_db/qdrant/DECISION.md`
- `vector_db/qdrant/SETUP_SPECS.md`

## Option 1: Embedded Local Mode

This mode does not require Docker.

Install dependencies:

```bash
pip install -e .
```

Initialize the local persisted collection:

```bash
.venv/bin/python scripts/setup_qdrant.py
```

Default local settings:

- collection: `customer_care_kb`
- embedding dimension: `1536`
- distance: `cosine`
- storage path: `vector_db/qdrant/data/local`

Optional environment variables:

```bash
export QDRANT_COLLECTION=customer_care_kb
export QDRANT_EMBEDDING_DIMENSION=1536
export QDRANT_DISTANCE=cosine
export QDRANT_PATH=vector_db/qdrant/data/local
```

## Option 2: Docker Mode

Start Qdrant as a service:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml up -d qdrant
```

This exposes:

- HTTP API on `http://localhost:6333`
- gRPC on `localhost:6334`

Persistent Docker storage is managed by Docker through the named volume:

- `qdrant_storage`

This is intentional. The original bind-mount approach was replaced because Docker on this machine rejected the host path as a shared mount location. Using a Docker-managed volume makes the standalone service more reliable across environments.

To point the setup script at Docker Qdrant:

```bash
export QDRANT_URL=http://localhost:6333
.venv/bin/python scripts/setup_qdrant.py
```

To verify the service:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml ps
curl http://localhost:6333/
```

## Recommended Choice For This Repo

For the first `kb_answer` RAG setup:

- embedded local mode is enough

If you want Qdrant to behave like a separate service from the start:

- Docker mode is a good choice

## Current Working State

The setup has already been validated in this repository:

- embedded local collection was created successfully
- Docker Qdrant was started successfully
- the HTTP endpoint responded on `http://localhost:6333`
