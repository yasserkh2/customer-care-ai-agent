# Steps Taken To Make The Vector DB Ready To Run

This document explains, step by step, what was done in this repository to make the vector database ready for use in the RAG implementation.

The current vector database choice is `Qdrant`.

## Goal

The goal was to make the project ready to:

- start a vector database locally
- keep the vector DB code separated from business services
- support both embedded local mode and Docker mode
- initialize a real collection that can later store embeddings for RAG

## Step 1: Chose Qdrant as the vector database

Qdrant was selected because it fits the project well:

- local-first development is easy
- metadata filtering is strong
- it works well with Python
- it has a clean path from prototype to production

Related docs added:

- `vector_db/qdrant/DECISION.md`
- `vector_db/qdrant/SETUP_SPECS.md`

## Step 2: Added the Qdrant Python dependency

The repository dependency list was updated in:

- `pyproject.toml`

Added package:

- `qdrant-client>=1.9.0`

This was required so the application can:

- connect to Qdrant
- create collections
- later insert and search vectors

## Step 3: Created a standalone `vector_db/` layer

Instead of mixing vector DB code into `app/services`, a separate infrastructure layer was introduced:

- `vector_db/`

This was done to keep the design more OOP-oriented and better separated.

The new structure includes:

- `vector_db/contracts.py`
- `vector_db/models.py`
- `vector_db/ARCHITECTURE.md`
- `vector_db/qdrant/`

## Step 4: Moved the vector DB interface out of `app/services`

The vector DB setup abstraction was moved into:

- `vector_db/contracts.py`

Current interface:

- `VectorDatabaseSetup`

This means the application can depend on a vector DB abstraction without tying the service layer to Qdrant-specific details.

## Step 5: Moved the vector DB setup result model into `vector_db`

The setup result model was moved into:

- `vector_db/models.py`

Current model:

- `VectorCollectionSetupResult`

This model returns information such as:

- collection name
- whether the collection was newly created
- backend path or URL
- embedding dimension
- distance metric

## Step 6: Added the Qdrant-specific implementation

The concrete Qdrant setup implementation was created in:

- `vector_db/qdrant/setup.py`

This file contains:

- `QdrantSettings`
- `QdrantVectorDatabaseSetup`

Responsibilities of this implementation:

- read Qdrant configuration from environment variables
- choose local path mode or remote URL mode
- create the Qdrant client
- create the collection if it does not already exist

## Step 7: Added environment-driven settings

The Qdrant setup reads configuration from environment variables.

Supported variables include:

- `QDRANT_COLLECTION`
- `QDRANT_EMBEDDING_DIMENSION`
- `QDRANT_DISTANCE`
- `QDRANT_PATH`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_PREFER_GRPC`

Default values were chosen so the project works immediately without extra setup.

Important defaults:

- collection: `customer_care_kb`
- embedding dimension: `1536`
- distance: `cosine`
- local path: `vector_db/qdrant/data/local`

## Step 8: Added a runnable setup script

A dedicated script was created:

- `scripts/setup_qdrant.py`

This script:

1. loads Qdrant settings
2. creates the vector DB setup object
3. ensures the collection exists
4. prints the setup result

This script is the main entry point for preparing the vector DB for the project.

## Step 9: Added Docker support

A Docker Compose file was added in:

- `vector_db/qdrant/docker-compose.yml`

This makes it possible to run Qdrant as a standalone service with:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml up -d qdrant
```

This mode exposes:

- HTTP on `localhost:6333`
- gRPC on `localhost:6334`

This is useful if you want the vector DB to run as a separate service instead of using embedded local mode.

Later, the Docker configuration was improved to use a Docker-managed named volume instead of a host bind mount, because the original host path was rejected by Docker file-sharing rules on this machine.

## Step 10: Added local persisted storage inside the vector DB directory

The local default storage path was set to:

- `vector_db/qdrant/data/local`

This was done so the vector DB stays inside its own standalone directory and does not spread runtime data around the repo root.

For Docker mode, persistence is now handled by a Docker-managed named volume:

- `qdrant_storage`

## Step 11: Updated `.gitignore`

The ignore rules were updated to avoid committing generated runtime data and Python cache files.

Important ignored paths now include:

- `vector_db/qdrant/data/`
- `vector_db/qdrant/data/local/`
- `**/__pycache__/`

This keeps the repo clean while allowing the vector DB to store local data.

## Step 12: Updated packaging so `vector_db` is importable

The package discovery in:

- `pyproject.toml`

was updated to include:

- `vector_db*`

Also added:

- `vector_db/__init__.py`
- `vector_db/qdrant/__init__.py`

This ensures the new infrastructure layer can be imported correctly after installation.

## Step 13: Added documentation for the new architecture

Several Markdown files were added to explain the design and usage:

- `vector_db/ARCHITECTURE.md`
- `vector_db/qdrant/README.md`
- `vector_db/qdrant/DECISION.md`
- `vector_db/qdrant/SETUP_SPECS.md`

These explain:

- why the vector DB layer is separate
- why Qdrant was chosen
- what specs are needed locally and in production
- how to run Qdrant

## Step 14: Updated the main README

The root README was updated to reflect:

- the standalone `vector_db/` layer
- the Qdrant setup flow
- the current architecture split between `app/services` and `vector_db`

This keeps the main project documentation aligned with the new setup.

## Step 15: Installed the dependency and initialized the collection

To make the vector DB actually runnable, the following happened:

1. project dependencies were installed into the local virtual environment
2. the Qdrant setup script was executed

The setup script completed successfully and created the collection:

- collection: `customer_care_kb`
- distance: `cosine`
- embedding dimension: `1536`
- backend: `vector_db/qdrant/data/local`

That means the vector DB is now ready to be used by the next RAG steps.

## Step 16: Started the standalone Docker Qdrant service

After the embedded local collection was initialized, the standalone Docker service was also started successfully.

Command used:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml up -d qdrant
```

Result:

- container started successfully
- service became reachable on `http://localhost:6333`
- Qdrant reported version `1.17.1`

## Current Result

The repository is now ready for the next phase:

- ingesting FAQ and document data into Qdrant
- creating a vector search repository abstraction
- wiring retrieval into `kb_answer`

The vector DB is currently ready in both of these modes:

- embedded persisted mode
- standalone Docker service mode

## Command Used To Initialize It

```bash
.venv/bin/python scripts/setup_qdrant.py
```

## Optional Docker Command

If you want Qdrant running as a separate service instead of embedded local mode:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml up -d qdrant
export QDRANT_URL=http://localhost:6333
.venv/bin/python scripts/setup_qdrant.py
```

To verify the running standalone service:

```bash
docker compose -f vector_db/qdrant/docker-compose.yml ps
curl http://localhost:6333/
```

## Final Summary

To make the vector DB ready to run, the work was done in this order:

1. choose Qdrant
2. add the dependency
3. create a standalone `vector_db/` architecture
4. move the interface and models into `vector_db/`
5. add the Qdrant implementation
6. add the setup script
7. add Docker support
8. set local storage paths
9. update `.gitignore`
10. update packaging and docs
11. install dependencies
12. initialize the collection
13. start and verify the standalone Docker service

At this point, Qdrant is ready and the repo can move into ingestion and retrieval work for RAG.
