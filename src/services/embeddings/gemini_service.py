"""
Google Gemini Embeddings Service

Provides embeddings using Google's Gemini Embedding models.
More cost-effective than OpenAI while maintaining high quality.
Includes automatic rate limiting to stay within Gemini's rate limits.
"""

import logging
from typing import List, Optional
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import settings
from src.utils.logging_config import get_logger
from src.services.rate_limiting import get_rate_limiter

logger = get_logger(__name__)


class GeminiEmbeddingsService:
    """Production-ready Google Gemini embeddings service"""

    def __init__(self, model: str = "models/embedding-001"):
        """
        Initialize Gemini embeddings service.

        Args:
            model: Gemini embedding model to use (default: embedding-001)

        Available models:
        - models/embedding-001: 768 dimensions
        """
        self.model = model

        self.client = GoogleGenerativeAIEmbeddings(
            model=self.model,
            google_api_key=settings.gemini_api_key,
        )

        self.total_tokens_used = 0
        self.rate_limiter = get_rate_limiter()

        logger.info(
            f"GeminiEmbeddingsService initialized: {self.model} "
            f"(rate limiting: 3,500 RPM)"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents using Gemini.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (768 dimensions each)
        """
        # Apply rate limiting
        delay = self.rate_limiter.request("gemini_embeddings")

        embeddings = self.client.embed_documents(texts)

        # Track tokens (rough estimate: ~1 token per word, ~5 words per 10 chars)
        estimated_tokens = sum(len(text) // 10 for text in texts) if texts else 0
        self.total_tokens_used += estimated_tokens

        logger.info(
            f"Embedded {len(texts)} documents with Gemini (~{estimated_tokens} tokens, "
            f"rate limit delay: {delay:.3f}s)"
        )

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query using Gemini.

        Args:
            query: Query text

        Returns:
            Embedding vector (768 dimensions)
        """
        # Apply rate limiting
        delay = self.rate_limiter.request("gemini_embeddings")

        embedding = self.client.embed_query(query)

        # Track tokens
        estimated_tokens = len(query) // 10
        self.total_tokens_used += estimated_tokens

        logger.info(f"Embedded query with Gemini (~{estimated_tokens} tokens, rate limit delay: {delay:.3f}s)")

        return embedding

    def get_cost_estimate(self) -> float:
        """
        Calculate estimated cost for tokens used.

        Gemini Embeddings pricing:
        - 1,000 requests per day free tier
        - $0.00001 per 1,000 tokens (production)

        Returns:
            Cost in USD
        """
        # Gemini pricing: $0.00001 per 1k tokens
        price_per_1k = 0.00001
        return (self.total_tokens_used / 1000) * price_per_1k

    def reset_cost_tracking(self) -> None:
        """Reset token counter"""
        self.total_tokens_used = 0


# Cached instance for efficiency
@lru_cache(maxsize=1)
def get_gemini_embeddings_service(model: str = "models/embedding-001") -> GeminiEmbeddingsService:
    """
    Get or create Gemini embeddings service (cached).

    Args:
        model: Gemini embedding model

    Returns:
        GeminiEmbeddingsService instance
    """
    return GeminiEmbeddingsService(model=model)
