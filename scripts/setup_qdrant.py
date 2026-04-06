from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_runtime_config
from vector_db.contracts import VectorDatabaseSetup
from vector_db.qdrant.setup import QdrantSettings, QdrantVectorDatabaseSetup


def main() -> None:
    load_runtime_config(
        config_path=PROJECT_ROOT / "config.yml",
        env_path=PROJECT_ROOT / ".env",
    )

    settings = QdrantSettings.from_env()
    vector_database: VectorDatabaseSetup = QdrantVectorDatabaseSetup(settings)
    result = vector_database.ensure_collection()

    status = "created" if result.created else "already exists"
    print("Qdrant setup complete.")
    print(f"Collection: {result.collection_name}")
    print(f"Status: {status}")
    print(f"Distance: {result.distance}")
    print(f"Embedding dimension: {result.embedding_dimension}")
    print(f"Backend: {result.backend}")


if __name__ == "__main__":
    main()
