"""
Embeddings Factory

Factory pattern to create embeddings service based on provider configuration.
Supports both OpenAI and Google Gemini embeddings.
"""

import logging
from typing import Optional, Union
from functools import lru_cache

from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_embeddings_service(provider: Optional[str] = None):
    """
    Create embeddings service based on provider configuration.

    Args:
        provider: Embeddings provider ('gemini' or 'openai'). If None, uses settings.embeddings_provider

    Returns:
        Embeddings service instance (GeminiEmbeddingsService or EmbeddingsService)

    Examples:
        # Use configured provider (default: Gemini)
        embeddings = create_embeddings_service()

        # Or override with specific provider
        embeddings = create_embeddings_service(provider='openai')
    """
    provider = provider or settings.embeddings_provider
    provider = provider.lower()

    if provider == 'gemini':
        from src.services.embeddings.gemini_service import GeminiEmbeddingsService
        logger.info(f"Creating GeminiEmbeddingsService for embeddings")
        return GeminiEmbeddingsService()

    elif provider == 'openai':
        from src.services.embeddings.openai_service import EmbeddingsService
        logger.info(f"Creating EmbeddingsService (OpenAI) for embeddings")
        return EmbeddingsService(use_large=True)

    else:
        raise ValueError(f"Unsupported embeddings provider: {provider}. Must be 'gemini' or 'openai'")


@lru_cache(maxsize=1)
def get_embeddings_service(provider: Optional[str] = None):
    """
    Get or create cached embeddings service.

    Args:
        provider: Embeddings provider ('gemini' or 'openai'). If None, uses settings.embeddings_provider

    Returns:
        Cached embeddings service instance
    """
    provider = provider or settings.embeddings_provider
    return create_embeddings_service(provider=provider)
