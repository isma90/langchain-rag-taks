"""
Retriever Factory

Creates and configures different retrieval strategies.
Supports: similarity search, MMR, and filtering.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from langchain_core.retrievers import BaseRetriever
from src.services.vector_store.qdrant_manager import QdrantVectorStoreManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RetrieverType(Enum):
    """Supported retriever types"""
    SIMILARITY = "similarity"
    MMR = "mmr"  # Maximum Marginal Relevance
    SIMILARITY_WITH_FILTER = "similarity_with_filter"


class RetrieverFactory:
    """
    Factory for creating optimized retrievers.

    Strategies:
    - Similarity: Simple vector similarity (fast, baseline)
    - MMR: Maximum Marginal Relevance (diverse results)
    - Filtered: Similarity with metadata filters
    """

    def __init__(self, vector_store_manager: QdrantVectorStoreManager):
        """
        Initialize retriever factory.

        Args:
            vector_store_manager: QdrantVectorStoreManager instance
        """
        self.vector_store_manager = vector_store_manager
        logger.info("RetrieverFactory initialized")

    def create_similarity_retriever(
        self,
        collection_name: str,
        k: int = 5,
    ) -> BaseRetriever:
        """
        Create simple similarity-based retriever.

        Args:
            collection_name: Qdrant collection name
            k: Number of results to return

        Returns:
            Configured retriever

        Usage:
            factory = RetrieverFactory(manager)
            retriever = factory.create_similarity_retriever("rag_documents", k=5)
            docs = retriever.invoke("what is AI?")
        """
        logger.info(f"Creating similarity retriever for {collection_name} (k={k})")

        return self.vector_store_manager.create_retriever(
            collection_name=collection_name,
            search_kwargs={"k": k},
        )

    def create_mmr_retriever(
        self,
        collection_name: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
    ) -> BaseRetriever:
        """
        Create Maximum Marginal Relevance retriever.

        MMR balances relevance with diversity.
        Good for avoiding redundant results.

        Args:
            collection_name: Qdrant collection name
            k: Final number of results
            fetch_k: Number of candidates to consider
            lambda_mult: 0-1, balance between relevance (1.0) and diversity (0.0)

        Returns:
            Configured retriever
        """
        logger.info(
            f"Creating MMR retriever for {collection_name} "
            f"(k={k}, fetch_k={fetch_k}, lambda={lambda_mult})"
        )

        return self.vector_store_manager.create_retriever(
            collection_name=collection_name,
            search_kwargs={
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
            },
        )

    def create_filtered_retriever(
        self,
        collection_name: str,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> BaseRetriever:
        """
        Create retriever with metadata filtering.

        Allows filtering by topic, complexity, sentiment, etc.

        Args:
            collection_name: Qdrant collection name
            k: Number of results
            metadata_filter: Filter dictionary (e.g., {"topic": "machine-learning"})

        Returns:
            Configured retriever with filters

        Example:
            retriever = factory.create_filtered_retriever(
                "rag_documents",
                k=5,
                metadata_filter={"topic": "AI", "complexity": "medium"}
            )
        """
        logger.info(
            f"Creating filtered retriever for {collection_name} "
            f"with filter: {metadata_filter}"
        )

        search_kwargs = {"k": k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter

        return self.vector_store_manager.create_retriever(
            collection_name=collection_name,
            search_kwargs=search_kwargs,
        )

    def create_adaptive_retriever(
        self,
        collection_name: str,
        k: int = 5,
        use_mmr: bool = False,
        use_filters: bool = False,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> BaseRetriever:
        """
        Create adaptive retriever with configurable parameters.

        Args:
            collection_name: Qdrant collection name
            k: Number of results
            use_mmr: Use MMR instead of simple similarity
            use_filters: Apply metadata filters
            metadata_filter: Filter dictionary

        Returns:
            Configured retriever
        """
        if use_mmr and use_filters:
            logger.info("Creating adaptive retriever (MMR + filters)")
            search_kwargs = {
                "k": k,
                "fetch_k": k * 4,
                "lambda_mult": 0.5,
            }
            if metadata_filter:
                search_kwargs["filter"] = metadata_filter

        elif use_mmr:
            logger.info("Creating adaptive retriever (MMR)")
            search_kwargs = {
                "k": k,
                "fetch_k": k * 4,
                "lambda_mult": 0.5,
            }

        elif use_filters:
            logger.info("Creating adaptive retriever (filters)")
            search_kwargs = {"k": k}
            if metadata_filter:
                search_kwargs["filter"] = metadata_filter

        else:
            logger.info("Creating adaptive retriever (simple similarity)")
            search_kwargs = {"k": k}

        return self.vector_store_manager.create_retriever(
            collection_name=collection_name,
            search_kwargs=search_kwargs,
        )

    def get_recommended_retriever(
        self,
        collection_name: str,
        query_type: str = "general",
    ) -> BaseRetriever:
        """
        Get recommended retriever based on query type.

        Query types:
        - general: Simple similarity (fast)
        - research: MMR (diverse results)
        - specific: Filtered (domain-specific)
        - complex: MMR + filters (best quality)

        Args:
            collection_name: Qdrant collection
            query_type: Type of query

        Returns:
            Recommended retriever configuration
        """
        recommendations = {
            "general": {
                "use_mmr": False,
                "use_filters": False,
                "k": 5,
            },
            "research": {
                "use_mmr": True,
                "use_filters": False,
                "k": 5,
            },
            "specific": {
                "use_mmr": False,
                "use_filters": True,
                "k": 3,
            },
            "complex": {
                "use_mmr": True,
                "use_filters": True,
                "k": 5,
            },
        }

        config = recommendations.get(query_type, recommendations["general"])

        logger.info(f"Using recommended retriever for '{query_type}' query: {config}")

        return self.create_adaptive_retriever(
            collection_name=collection_name,
            **config,
        )
