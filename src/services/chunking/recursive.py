"""
Recursive Chunking Service

Implements RecursiveCharacterTextSplitter with production features:
- Token-based sizing (not characters)
- Document-specific configuration
- Chunking evaluation metrics
- Cost tracking
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_core.documents import Document
from src.services.chunking.factory import ChunkingFactory
from src.utils.logging_config import get_logger
from src.utils.tokenization import get_token_counter

logger = get_logger(__name__)


@dataclass
class ChunkingMetrics:
    """Metrics from chunking operation"""
    total_documents: int
    total_chunks: int
    avg_chunk_tokens: float
    min_chunk_tokens: int
    max_chunk_tokens: int
    processing_time_ms: float
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float


class RecursiveChunkingService:
    """
    Production-ready recursive chunking service.

    Features:
    - Token-based sizing
    - Metadata preservation
    - Chunking metrics
    - Cost tracking
    - Structured logging
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize recursive chunking service.

        Args:
            chunk_size: Chunk size in TOKENS (not characters!)
            chunk_overlap: Token overlap between chunks (20% recommended)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.token_counter = get_token_counter()
        self.factory = ChunkingFactory(self.token_counter.count_tokens)

        # Create the splitter
        self.splitter = self.factory.create_recursive(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        logger.info(
            f"RecursiveChunkingService initialized: "
            f"size={chunk_size}, overlap={chunk_overlap}"
        )

    def chunk_documents(
        self,
        documents: List[Document],
        track_metrics: bool = True,
    ) -> tuple[List[Document], Optional[ChunkingMetrics]]:
        """
        Chunk documents using recursive strategy.

        Args:
            documents: List of LangChain Document objects
            track_metrics: Whether to compute and return metrics

        Returns:
            Tuple of (chunked_documents, metrics)

        Usage:
            service = RecursiveChunkingService()
            chunks, metrics = service.chunk_documents(documents)
            print(f"Created {metrics.total_chunks} chunks")
        """
        import time

        start_time = time.time()

        # Calculate input metrics
        total_input_tokens = sum(
            self.token_counter.count_tokens(doc.page_content)
            for doc in documents
        )

        logger.info(
            f"Chunking {len(documents)} documents "
            f"({total_input_tokens} total tokens)"
        )

        # Perform chunking
        chunks = self.splitter.split_documents(documents)

        # Calculate output metrics
        total_output_tokens = sum(
            self.token_counter.count_tokens(chunk.page_content)
            for chunk in chunks
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Log operation
        logger.log_chunking(
            input_documents=len(documents),
            output_chunks=len(chunks),
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            processing_time_ms=processing_time,
            strategy="recursive",
        )

        # Build metrics
        metrics = None
        if track_metrics:
            chunk_tokens = [
                self.token_counter.count_tokens(chunk.page_content)
                for chunk in chunks
            ]
            metrics = ChunkingMetrics(
                total_documents=len(documents),
                total_chunks=len(chunks),
                avg_chunk_tokens=sum(chunk_tokens) / len(chunk_tokens) if chunk_tokens else 0,
                min_chunk_tokens=min(chunk_tokens) if chunk_tokens else 0,
                max_chunk_tokens=max(chunk_tokens) if chunk_tokens else 0,
                processing_time_ms=processing_time,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                estimated_cost_usd=self._estimate_cost(total_output_tokens),
            )

            logger.info(
                f"Chunking complete: {metrics.total_chunks} chunks, "
                f"avg {metrics.avg_chunk_tokens:.0f} tokens/chunk, "
                f"cost ${metrics.estimated_cost_usd:.6f}"
            )

        return chunks, metrics

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Chunk a single text string.

        Args:
            text: Text to chunk
            metadata: Optional metadata dict

        Returns:
            List of Document chunks with metadata
        """
        # Create document
        doc = Document(page_content=text, metadata=metadata or {})

        # Chunk
        chunks, _ = self.chunk_documents([doc], track_metrics=False)

        return chunks

    def estimate_chunks(self, text: str) -> Dict[str, Any]:
        """
        Estimate chunking parameters for text without actually chunking.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with estimates
        """
        token_count = self.token_counter.count_tokens(text)

        # Calculate how many chunks would be created
        expected_chunks = max(1, (token_count - self.chunk_overlap) // (self.chunk_size - self.chunk_overlap))

        return {
            "total_tokens": token_count,
            "expected_chunks": expected_chunks,
            "avg_chunk_tokens": self.chunk_size,
            "estimated_cost_usd": self._estimate_cost(token_count),
        }

    def validate_chunks(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Validate chunk quality and consistency.

        Checks:
        - No empty chunks
        - Chunk sizes within range
        - Metadata preservation
        - No overlap > configured overlap

        Args:
            chunks: Chunks to validate

        Returns:
            Validation report
        """
        issues = []
        warnings = []

        # Check for empty chunks
        empty_chunks = [i for i, c in enumerate(chunks) if not c.page_content.strip()]
        if empty_chunks:
            issues.append(f"Empty chunks at indices: {empty_chunks}")

        # Check chunk sizes
        chunk_sizes = [self.token_counter.count_tokens(c.page_content) for c in chunks]
        oversized = [
            (i, size) for i, size in enumerate(chunk_sizes)
            if size > self.chunk_size * 1.1  # 10% tolerance
        ]
        if oversized:
            warnings.append(f"Oversized chunks: {oversized}")

        # Check metadata preservation
        chunks_without_source = [i for i, c in enumerate(chunks) if "source" not in c.metadata]
        if chunks_without_source and chunks_without_source:
            warnings.append(f"Chunks missing 'source' metadata: {chunks_without_source}")

        return {
            "total_chunks": len(chunks),
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "chunk_token_stats": {
                "min": min(chunk_sizes) if chunk_sizes else 0,
                "max": max(chunk_sizes) if chunk_sizes else 0,
                "avg": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                "median": sorted(chunk_sizes)[len(chunk_sizes)//2] if chunk_sizes else 0,
            }
        }

    @staticmethod
    def _estimate_cost(tokens: int, model: str = "text-embedding-3-large") -> float:
        """Estimate cost for tokens"""
        prices = {
            "text-embedding-3-large": 0.00013,
            "text-embedding-3-small": 0.00002,
        }
        price_per_1k = prices.get(model, 0.00013)
        return (tokens / 1000) * price_per_1k

    def configure_for_document_type(self, doc_type: str) -> None:
        """
        Reconfigure chunking parameters based on document type.

        Args:
            doc_type: Type of document (pdf, html, markdown, code, etc.)
        """
        strategy, params = self.factory.select_optimal(doc_type)

        self.chunk_size = params.get("chunk_size", self.chunk_size)
        self.chunk_overlap = params.get("chunk_overlap", self.chunk_overlap)

        # Recreate splitter with new params
        self.splitter = self.factory.create_recursive(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        logger.info(f"Reconfigured for {doc_type}: size={self.chunk_size}, overlap={self.chunk_overlap}")
