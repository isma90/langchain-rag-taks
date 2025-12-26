"""
OpenAI Embeddings Service

Provides unified embeddings service with cost tracking and caching.
Includes automatic rate limiting to stay within OpenAI's 3,500 RPM tier.
"""

import logging
from typing import List, Optional
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from src.config import settings
from src.utils.logging_config import get_logger
from src.services.rate_limiting import get_rate_limiter

logger = get_logger(__name__)


class EmbeddingsService:
    """Production-ready OpenAI embeddings service"""

    def __init__(self, use_large: bool = True):
        """
        Initialize embeddings service.

        Args:
            use_large: Use text-embedding-3-large (True) or text-embedding-3-small (False)
        """
        self.use_large = use_large
        self.model = "text-embedding-3-large" if use_large else "text-embedding-3-small"

        # Dimension reduction for cost optimization
        # text-embedding-3-large: 3072 dims → 512 (95% quality, 6x smaller)
        # text-embedding-3-small: 1536 dims → 256 (95% quality, 6x smaller)
        self.dimensions = 512 if use_large else 256

        self.client = OpenAIEmbeddings(
            model=self.model,
            dimensions=self.dimensions,
            api_key=settings.openai_api_key,
            max_retries=3,  # Retry on rate limit (429) with exponential backoff
        )

        self.total_tokens_used = 0
        self.rate_limiter = get_rate_limiter()

        logger.info(
            f"EmbeddingsService initialized: {self.model} "
            f"with {self.dimensions} dimensions (rate limiting: 3,500 RPM)"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Apply rate limiting
        delay = self.rate_limiter.request("embeddings")

        embeddings = self.client.embed_documents(texts)

        # Track tokens (rough estimate: ~1 token per word, ~5 words per 10 chars)
        estimated_tokens = sum(len(text) // 10 for text in texts) if texts else 0
        self.total_tokens_used += estimated_tokens

        logger.info(
            f"Embedded {len(texts)} documents (~{estimated_tokens} tokens, "
            f"rate limit delay: {delay:.3f}s)"
        )

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        # Apply rate limiting
        delay = self.rate_limiter.request("embeddings")

        embedding = self.client.embed_query(query)

        # Track tokens
        estimated_tokens = len(query) // 10
        self.total_tokens_used += estimated_tokens

        logger.info(f"Embedded query (~{estimated_tokens} tokens, rate limit delay: {delay:.3f}s)")

        return embedding

    def get_cost_estimate(self) -> float:
        """
        Calculate estimated cost for tokens used.

        Returns:
            Cost in USD
        """
        prices = {
            "text-embedding-3-large": 0.00013,
            "text-embedding-3-small": 0.00002,
        }
        price_per_1k = prices.get(self.model, 0.00013)
        return (self.total_tokens_used / 1000) * price_per_1k

    def reset_cost_tracking(self) -> None:
        """Reset token counter"""
        self.total_tokens_used = 0


# Cached instances for efficiency
@lru_cache(maxsize=2)
def get_embeddings_service(use_large: bool = True) -> EmbeddingsService:
    """
    Get or create embeddings service (cached).

    Args:
        use_large: Use large model (True) or small model (False)

    Returns:
        EmbeddingsService instance
    """
    return EmbeddingsService(use_large=use_large)
