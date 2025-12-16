"""
Semantic Chunking Service

Uses embeddings to find natural topic boundaries for maximum quality.
More expensive (60-70% more tokens) but significantly better results.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from src.services.embeddings.openai_service import EmbeddingsService
from src.utils.logging_config import get_logger
from src.utils.tokenization import get_token_counter

logger = get_logger(__name__)


@dataclass
class SemanticChunkingMetrics:
    """Metrics from semantic chunking"""
    total_documents: int
    total_chunks: int
    processing_time_ms: float
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    embedding_cost_usd: float
    total_cost_usd: float


class SemanticChunkingService:
    """
    Production-ready semantic chunking service.

    Uses embeddings to find natural topic boundaries.
    Premium option: 60-70% more tokens but highest quality.

    Features:
    - Automatic topic boundary detection
    - Metadata preservation
    - Cost tracking (includes embedding cost)
    - Structured logging
    """

    def __init__(
        self,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: int = 50,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize semantic chunking service.

        Args:
            breakpoint_threshold_type: "percentile" or "standard_deviation"
            breakpoint_threshold_amount: Threshold amount (50 for percentile)
            embedding_model: Embedding model to use for similarity
        """
        self.embedding_model = embedding_model
        self.breakpoint_threshold_type = breakpoint_threshold_type
        self.breakpoint_threshold_amount = breakpoint_threshold_amount
        self.token_counter = get_token_counter()

        # Initialize embeddings service (uses smaller model for cost)
        self.embeddings_service = EmbeddingsService(use_large=False)

        # Create semantic chunker
        self.chunker = SemanticChunker(
            embeddings=self.embeddings_service.client,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount,
        )

        logger.info(
            f"SemanticChunkingService initialized with {embedding_model} "
            f"(threshold: {breakpoint_threshold_amount})"
        )

    def chunk_documents(
        self,
        documents: List[Document],
        track_metrics: bool = True,
    ) -> tuple[List[Document], Optional[SemanticChunkingMetrics]]:
        """
        Chunk documents using semantic similarity.

        Process:
        1. Calculate embeddings for sentences
        2. Find breakpoints where similarity drops significantly
        3. Create chunks at natural topic boundaries

        Args:
            documents: List of LangChain Document objects
            track_metrics: Whether to compute and return metrics

        Returns:
            Tuple of (chunked_documents, metrics)

        Usage:
            service = SemanticChunkingService()
            chunks, metrics = service.chunk_documents(documents)
            print(f"Cost: ${metrics.total_cost_usd:.6f}")
        """
        import time

        start_time = time.time()

        # Calculate input metrics
        total_input_tokens = sum(
            self.token_counter.count_tokens(doc.page_content)
            for doc in documents
        )

        logger.info(
            f"Semantic chunking {len(documents)} documents "
            f"({total_input_tokens} total tokens)"
        )

        # Combine all document text
        combined_text = "\n\n".join(doc.page_content for doc in documents)

        # Perform semantic chunking
        chunks_text = self.chunker.split_text(combined_text)

        # Convert back to Document objects with metadata
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            # Try to preserve original source metadata
            metadata = {
                "chunk_index": i,
                "chunking_strategy": "semantic",
            }

            # Copy metadata from first document if available
            if documents:
                metadata.update(documents[0].metadata)

            chunks.append(Document(page_content=chunk_text, metadata=metadata))

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate output metrics
        total_output_tokens = sum(
            self.token_counter.count_tokens(chunk.page_content)
            for chunk in chunks
        )

        # Log operation
        logger.info(
            f"Semantic chunking complete: {len(chunks)} chunks "
            f"({total_output_tokens} tokens)"
        )

        # Build metrics
        metrics = None
        if track_metrics:
            embedding_cost = self._calculate_embedding_cost(total_input_tokens)
            chunk_cost = self._estimate_chunk_cost(total_output_tokens)
            total_cost = embedding_cost + chunk_cost

            metrics = SemanticChunkingMetrics(
                total_documents=len(documents),
                total_chunks=len(chunks),
                processing_time_ms=processing_time,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                estimated_cost_usd=chunk_cost,
                embedding_cost_usd=embedding_cost,
                total_cost_usd=total_cost,
            )

            logger.info(
                f"Semantic chunking metrics: "
                f"chunks={metrics.total_chunks}, "
                f"cost=${metrics.total_cost_usd:.6f} "
                f"(embedding: ${metrics.embedding_cost_usd:.6f})"
            )

        return chunks, metrics

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Chunk a single text string semantically.

        Args:
            text: Text to chunk
            metadata: Optional metadata dict

        Returns:
            List of Document chunks
        """
        doc = Document(page_content=text, metadata=metadata or {})
        chunks, _ = self.chunk_documents([doc], track_metrics=False)
        return chunks

    def compare_with_recursive(
        self,
        documents: List[Document],
    ) -> Dict[str, Any]:
        """
        Compare semantic chunking with recursive chunking.

        Returns metrics for both methods so you can decide which to use.

        Args:
            documents: Documents to chunk

        Returns:
            Comparison report with costs
        """
        from src.services.chunking.recursive import RecursiveChunkingService

        # Semantic chunking
        semantic_chunks, semantic_metrics = self.chunk_documents(documents)

        # Recursive chunking (for comparison)
        recursive_service = RecursiveChunkingService()
        recursive_chunks, recursive_metrics = recursive_service.chunk_documents(documents)

        return {
            "semantic": {
                "chunks": len(semantic_chunks),
                "cost": semantic_metrics.total_cost_usd if semantic_metrics else 0,
                "metrics": semantic_metrics,
            },
            "recursive": {
                "chunks": len(recursive_chunks),
                "cost": recursive_metrics.estimated_cost_usd if recursive_metrics else 0,
                "metrics": recursive_metrics,
            },
            "recommendation": self._get_recommendation(
                semantic_metrics,
                recursive_metrics,
            ),
        }

    @staticmethod
    def _calculate_embedding_cost(tokens: int, model: str = "text-embedding-3-small") -> float:
        """Calculate cost for embeddings"""
        # For semantic chunking, we need embeddings for sentences
        # Roughly 1 embedding per sentence, ~10 tokens per sentence
        # Estimate: tokens / 10 embeddings needed
        estimated_embedding_tokens = tokens / 10  # Very rough estimate
        price_per_1k = 0.00002  # text-embedding-3-small price
        return (estimated_embedding_tokens / 1000) * price_per_1k

    @staticmethod
    def _estimate_chunk_cost(tokens: int, model: str = "text-embedding-3-small") -> float:
        """Estimate cost for chunk embeddings (final vectors)"""
        price_per_1k = 0.00002  # text-embedding-3-small
        return (tokens / 1000) * price_per_1k

    @staticmethod
    def _get_recommendation(semantic_metrics, recursive_metrics) -> str:
        """Get recommendation on which strategy to use"""
        if not semantic_metrics or not recursive_metrics:
            return "Unable to provide recommendation"

        cost_diff_percent = (
            (semantic_metrics.total_cost_usd - recursive_metrics.estimated_cost_usd)
            / recursive_metrics.estimated_cost_usd
            * 100
        )

        if cost_diff_percent > 100:  # More than 100% more expensive
            return (
                f"Use Recursive: Semantic is {cost_diff_percent:.0f}% more expensive. "
                "Good for quick prototyping. Switch to Semantic only if quality is insufficient."
            )
        else:
            return (
                f"Consider Semantic: Only {cost_diff_percent:.0f}% more expensive. "
                "Better quality for complex documents. Worth the cost for production."
            )
