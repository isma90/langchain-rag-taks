"""Retrievers Service Package

Provides different retriever strategies: similarity, MMR, filtered, and adaptive.
"""

from src.services.retrievers.factory import RetrieverFactory, RetrieverType

__all__ = [
    'RetrieverFactory',
    'RetrieverType'
]
