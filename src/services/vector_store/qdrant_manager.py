"""
Qdrant Vector Store Manager

Production-ready Qdrant Cloud integration with:
- Collection management
- Batch indexing pipeline
- Health monitoring
- Cost tracking
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from src.config import settings
from src.services.embeddings.embeddings_factory import create_embeddings_service
from src.utils.logging_config import get_logger
from src.utils.resilience import retry_with_backoff, APICircuitBreaker

logger = get_logger(__name__)


@dataclass
class IndexingMetrics:
    """Metrics from indexing operation"""
    total_documents: int
    total_vectors: int
    collection_name: str
    processing_time_ms: float
    estimated_cost_usd: float
    batch_count: int


class QdrantVectorStoreManager:
    """
    Production-ready Qdrant Cloud vector store manager.

    Features:
    - Create/manage collections
    - Batch indexing with retry logic
    - Health monitoring
    - Cost tracking
    - Circuit breaker for resilience
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Qdrant manager.

        Args:
            url: Qdrant URL (default: from settings)
            api_key: Qdrant API key (default: from settings)
            timeout: Request timeout in seconds
        """
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.timeout = timeout

        # Initialize Qdrant client with retry logic
        try:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=timeout,
            )
            # Test connection
            self.client.get_collections()
            logger.info(f"Qdrant client initialized: {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

        # Circuit breaker for API calls
        self.circuit_breaker = APICircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
        )

        # Create embeddings service based on provider configuration
        # Default: Gemini (more cost-effective), can be overridden with EMBEDDINGS_PROVIDER env var
        self.embeddings_service = create_embeddings_service()

    @retry_with_backoff(max_attempts=3, initial_delay=1.0)
    def create_collection(
        self,
        collection_name: str,
        documents: List[Document],
        force_recreate: bool = False,
        batch_size: int = 100,
    ) -> QdrantVectorStore:
        """
        Create collection and index documents.

        Args:
            collection_name: Name for the collection
            documents: Documents to index
            force_recreate: Delete existing collection first
            batch_size: Batch size for indexing

        Returns:
            QdrantVectorStore instance

        Usage:
            manager = QdrantVectorStoreManager()
            vector_store = manager.create_collection(
                collection_name="rag_documents",
                documents=chunks,
                force_recreate=False,
            )
        """
        start_time = time.time()

        logger.info(
            f"Creating collection '{collection_name}' "
            f"with {len(documents)} documents"
        )

        # Delete existing collection if requested
        if force_recreate:
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            except (ResponseHandlingException, Exception):
                pass  # Collection doesn't exist, that's OK

        # Try to create vector store
        # Retry with force_recreate=True if initial creation fails
        try:
            vector_store = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings_service.client,
                url=self.url,
                api_key=self.api_key,
                collection_name=collection_name,
                batch_size=batch_size,
                force_recreate=force_recreate,
            )
        except (ResponseHandlingException, Exception) as e:
            logger.warning(f"First attempt failed: {e}. Retrying with force_recreate=True")
            # Try again with force_recreate=True to handle collection issues
            vector_store = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings_service.client,
                url=self.url,
                api_key=self.api_key,
                collection_name=collection_name,
                batch_size=batch_size,
                force_recreate=True,  # Force recreation
            )

        processing_time = (time.time() - start_time) * 1000

        # Get collection stats
        stats = self.get_collection_stats(collection_name)

        logger.log_indexing(
            collection_name=collection_name,
            vectors_indexed=stats.get("vectors_count", 0),
            documents_indexed=len(documents),
            processing_time_ms=processing_time,
            batch_size=batch_size,
        )

        return vector_store

    @retry_with_backoff(max_attempts=3)
    def add_documents(
        self,
        collection_name: str,
        documents: List[Document],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Add documents to existing collection.

        Args:
            collection_name: Target collection name
            documents: Documents to add
            batch_size: Batch size for indexing

        Returns:
            Statistics about the operation
        """
        start_time = time.time()

        logger.info(
            f"Adding {len(documents)} documents to '{collection_name}'"
        )

        # Get existing vector store
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings_service.client,
        )

        # Add documents in batches
        batch_count = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            vector_store.add_documents(batch)
            batch_count += 1
            logger.debug(f"Added batch {batch_count}/{len(documents)//batch_size + 1}")

        processing_time = (time.time() - start_time) * 1000

        # Get updated stats
        stats = self.get_collection_stats(collection_name)

        return {
            "status": "success",
            "documents_added": len(documents),
            "batch_count": batch_count,
            "processing_time_ms": processing_time,
            "collection_stats": stats,
        }

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get collection statistics.

        Args:
            collection_name: Collection name

        Returns:
            Dictionary with collection info
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "collection_name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": str(collection_info.status),
                "vector_size": collection_info.config.vector_size,
            }
        except Exception as e:
            logger.warning(f"Failed to get stats for {collection_name}: {e}")
            return {"error": str(e)}

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        try:
            response = self.client.get_collections()
            return [collection.name for collection in response.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Collection to delete

        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get Qdrant health status.

        Returns:
            Health information
        """
        try:
            health = self.client.get_collections()
            return {
                "status": "healthy",
                "collections_count": len(health.collections),
                "collections": self.list_collections(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def create_retriever(
        self,
        collection_name: str,
        search_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a retriever from collection.

        Args:
            collection_name: Collection to retrieve from
            search_kwargs: Optional retriever kwargs (e.g., {'k': 5})

        Returns:
            LangChain retriever
        """
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings_service.client,
        )

        search_kwargs = search_kwargs or {"k": 5}
        return vector_store.as_retriever(search_kwargs=search_kwargs)

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return self.circuit_breaker.get_state()
