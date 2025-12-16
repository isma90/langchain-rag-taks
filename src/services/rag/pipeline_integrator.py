"""
RAG Pipeline Integrator

Integrates document loading, chunking, metadata extraction, vector indexing,
and retrieval into a complete production-ready pipeline.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.documents import Document
from src.services.chunking.factory import ChunkingFactory, ChunkingStrategy
from src.services.vector_store.qdrant_manager import QdrantVectorStoreManager
from src.services.vector_store.metadata_handler import MetadataHandler
from src.services.retrievers.factory import RetrieverFactory
from src.utils.logging_config import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


@dataclass
class PipelineMetrics:
    """Metrics from complete pipeline execution"""
    total_documents: int
    total_chunks: int
    total_vectors: int
    collection_name: str
    total_processing_time_ms: float
    chunking_time_ms: float
    metadata_extraction_time_ms: float
    indexing_time_ms: float
    estimated_cost_usd: float
    retrieval_strategy: str


class RAGPipelineIntegrator:
    """
    Production-ready RAG pipeline integrator.

    Orchestrates the complete pipeline:
    1. Document loading (external)
    2. Chunking (token-based)
    3. Metadata extraction (LLM-based)
    4. Vector indexing (Qdrant)
    5. Retrieval (multiple strategies)

    Usage:
        integrator = RAGPipelineIntegrator(collection_name="my_docs")
        documents = [...]  # Loaded documents
        metrics = integrator.process_documents(documents)
        retriever = integrator.get_retriever(query_type="research")
        results = retriever.invoke("what is AI?")
    """

    def __init__(
        self,
        collection_name: str = "rag_documents",
        use_metadata_extraction: bool = True,
        force_recreate_collection: bool = False,
    ):
        """
        Initialize RAG pipeline integrator.

        Args:
            collection_name: Qdrant collection name
            use_metadata_extraction: Extract metadata using LLM
            force_recreate_collection: Delete existing collection first
        """
        self.collection_name = collection_name
        self.use_metadata_extraction = use_metadata_extraction
        self.force_recreate_collection = force_recreate_collection

        # Initialize components
        self.chunking_factory = ChunkingFactory()
        self.vector_store_manager = QdrantVectorStoreManager()
        self.metadata_handler = MetadataHandler(use_structured_output=True)
        self.retriever_factory = RetrieverFactory(self.vector_store_manager)

        # Store processed documents and metrics
        self.processed_documents: List[Document] = []
        self.last_metrics: Optional[PipelineMetrics] = None

        logger.info(f"RAGPipelineIntegrator initialized for collection: {collection_name}")

    def process_documents(
        self,
        documents: List[Document],
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        enable_metadata_extraction: bool = None,
        chunk_size_tokens: int = None,
        overlap_tokens: int = None,
    ) -> PipelineMetrics:
        """
        Process documents through complete pipeline.

        Args:
            documents: List of Document objects to process
            chunking_strategy: Strategy for chunking (RECURSIVE, SEMANTIC, MARKDOWN, HTML)
            enable_metadata_extraction: Override global setting for this run
            chunk_size_tokens: Override default chunk size (tokens)
            overlap_tokens: Override default overlap (tokens)

        Returns:
            PipelineMetrics with processing details

        Usage:
            from langchain_core.documents import Document
            docs = [Document(page_content="...", metadata={"source": "..."})]
            metrics = integrator.process_documents(docs)
            print(f"Indexed {metrics.total_vectors} vectors in {metrics.total_processing_time_ms}ms")
        """
        start_time = time.time()
        logger.info(f"Starting pipeline: {len(documents)} documents")

        # Step 1: Chunk documents
        chunking_start = time.time()
        chunks = self._chunk_documents(
            documents,
            strategy=chunking_strategy,
            chunk_size_tokens=chunk_size_tokens,
            overlap_tokens=overlap_tokens,
        )
        chunking_time_ms = (time.time() - chunking_start) * 1000
        logger.info(f"Chunking complete: {len(chunks)} chunks in {chunking_time_ms:.1f}ms")

        # Step 2: Extract metadata (optional)
        metadata_time_ms = 0.0
        if enable_metadata_extraction is None:
            enable_metadata_extraction = self.use_metadata_extraction

        if enable_metadata_extraction:
            metadata_start = time.time()
            chunks = self.metadata_handler.enrich_documents(chunks)
            metadata_time_ms = (time.time() - metadata_start) * 1000
            logger.info(f"Metadata extraction complete in {metadata_time_ms:.1f}ms")

        # Step 3: Index documents in vector store
        indexing_start = time.time()
        indexing_metrics = self._index_documents(chunks)
        indexing_time_ms = (time.time() - indexing_start) * 1000

        # Store processed documents
        self.processed_documents = chunks

        # Calculate total metrics
        total_time_ms = (time.time() - start_time) * 1000
        total_cost = indexing_metrics.estimated_cost_usd

        self.last_metrics = PipelineMetrics(
            total_documents=len(documents),
            total_chunks=len(chunks),
            total_vectors=indexing_metrics.total_vectors,
            collection_name=self.collection_name,
            total_processing_time_ms=total_time_ms,
            chunking_time_ms=chunking_time_ms,
            metadata_extraction_time_ms=metadata_time_ms,
            indexing_time_ms=indexing_time_ms,
            estimated_cost_usd=total_cost,
            retrieval_strategy="standard",
        )

        logger.info(
            f"Pipeline complete: {self.last_metrics.total_vectors} vectors indexed "
            f"in {total_time_ms:.1f}ms (cost: ${total_cost:.4f})"
        )

        return self.last_metrics

    def _chunk_documents(
        self,
        documents: List[Document],
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        chunk_size_tokens: int = None,
        overlap_tokens: int = None,
    ) -> List[Document]:
        """
        Chunk documents using specified strategy.

        Args:
            documents: Documents to chunk
            strategy: Chunking strategy
            chunk_size_tokens: Override default chunk size (tokens)
            overlap_tokens: Override default overlap (tokens)

        Returns:
            List of chunked documents
        """
        chunk_size = chunk_size_tokens or settings.chunk_size_tokens
        overlap = overlap_tokens or settings.chunk_overlap_tokens

        if strategy == ChunkingStrategy.RECURSIVE:
            logger.debug(f"Using RECURSIVE chunking: size={chunk_size}, overlap={overlap}")
            # create_recursive returns a RecursiveCharacterTextSplitter directly
            splitter = self.chunking_factory.create_recursive(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
            )
            # Splitters use split_documents method
            chunks = splitter.split_documents(documents)
        elif strategy == ChunkingStrategy.SEMANTIC:
            logger.debug(f"Using SEMANTIC chunking: size={chunk_size}")
            # For semantic, we need to use RecursiveChunkingService
            from src.services.chunking.recursive import RecursiveChunkingService
            service = RecursiveChunkingService()
            chunks = service.chunk_documents(documents)
        elif strategy == ChunkingStrategy.MARKDOWN:
            logger.debug("Using MARKDOWN chunking")
            splitter = self.chunking_factory.create_markdown()
            chunks = splitter.split_documents(documents)
        elif strategy == ChunkingStrategy.HTML:
            logger.debug("Using HTML chunking")
            splitter = self.chunking_factory.create_html()
            chunks = splitter.split_documents(documents)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

        return chunks

    def _index_documents(self, chunks: List[Document]):
        """
        Index chunked documents in Qdrant.

        Args:
            chunks: Chunked documents to index

        Returns:
            IndexingMetrics with indexing details
        """
        logger.info(f"Indexing {len(chunks)} chunks into collection: {self.collection_name}")

        # Create or recreate collection
        vector_store = self.vector_store_manager.create_collection(
            collection_name=self.collection_name,
            documents=chunks,
            force_recreate=self.force_recreate_collection,
            batch_size=100,
        )

        # Get collection stats
        stats = self.vector_store_manager.get_collection_stats(self.collection_name)

        # Estimate cost (embeddings cost for chunks)
        vectors_indexed = stats.get("vectors_count", 0)
        estimated_cost = (vectors_indexed * 3072 / 1000) * 0.00013  # Rough estimate

        # Return metrics
        from src.services.vector_store.qdrant_manager import IndexingMetrics
        return IndexingMetrics(
            total_documents=len(chunks),
            total_vectors=vectors_indexed,
            collection_name=self.collection_name,
            processing_time_ms=0,  # Already calculated in manager
            estimated_cost_usd=estimated_cost,
            batch_count=len(chunks) // 100 + 1,
        )

    def get_retriever(
        self,
        query_type: str = "general",
        k: int = 5,
    ):
        """
        Get configured retriever for querying.

        Args:
            query_type: Type of query (general, research, specific, complex)
            k: Number of results to return

        Returns:
            Configured LangChain retriever

        Usage:
            retriever = integrator.get_retriever(query_type="research", k=5)
            results = retriever.invoke("what is machine learning?")
            for doc in results:
                print(doc.page_content)
        """
        return self.retriever_factory.get_recommended_retriever(
            collection_name=self.collection_name,
            query_type=query_type,
        )

    def get_adaptive_retriever(
        self,
        k: int = 5,
        use_mmr: bool = False,
        use_filters: bool = False,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ):
        """
        Get adaptive retriever with custom configuration.

        Args:
            k: Number of results
            use_mmr: Use Maximum Marginal Relevance
            use_filters: Apply metadata filters
            metadata_filter: Filter dictionary (e.g., {"topic": "AI"})

        Returns:
            Configured retriever

        Usage:
            retriever = integrator.get_adaptive_retriever(
                k=5,
                use_mmr=True,
                use_filters=True,
                metadata_filter={"complexity": "medium"}
            )
        """
        return self.retriever_factory.create_adaptive_retriever(
            collection_name=self.collection_name,
            k=k,
            use_mmr=use_mmr,
            use_filters=use_filters,
            metadata_filter=metadata_filter,
        )

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get current collection statistics.

        Returns:
            Dictionary with collection info
        """
        return self.vector_store_manager.get_collection_stats(self.collection_name)

    def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get health status of pipeline components.

        Returns:
            Health status dictionary
        """
        return {
            "vector_store_health": self.vector_store_manager.get_health_status(),
            "circuit_breaker_status": self.vector_store_manager.get_circuit_breaker_status(),
            "collection_stats": self.get_collection_stats(),
            "last_metrics": (
                self.last_metrics.__dict__ if self.last_metrics else None
            ),
        }

    def delete_collection(self) -> bool:
        """
        Delete the collection.

        Returns:
            True if successful
        """
        return self.vector_store_manager.delete_collection(self.collection_name)

    def list_collections(self) -> List[str]:
        """
        List all available collections.

        Returns:
            List of collection names
        """
        return self.vector_store_manager.list_collections()
