"""Vectorization package for turning text chunks into vector records."""

from processing.vectorization.contracts import EmbeddingGenerator, VectorizationStrategy
from processing.vectorization.faqs import FaqVectorizationStrategy
from processing.vectorization.local import DeterministicEmbeddingGenerator
from processing.vectorization.models import VectorizationResult

__all__ = [
    "DeterministicEmbeddingGenerator",
    "EmbeddingGenerator",
    "FaqVectorizationStrategy",
    "VectorizationResult",
    "VectorizationStrategy",
]
