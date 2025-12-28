"""
RAG Service

Complete end-to-end RAG service integrating:
- Pipeline initialization
- Document retrieval
- Question answering with multiple strategies
- Response formatting and tracking
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from langchain_core.documents import Document
from src.services.rag.pipeline_integrator import RAGPipelineIntegrator
from src.services.rag.chain_builder import RAGChainBuilder
from src.utils.logging_config import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG system"""
    answer: str
    query_type: str
    documents_used: int
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    sources: List[str]
    model: str


class RAGService:
    """
    Complete RAG service for question-answering.

    Pipeline:
    1. Initialize collection with documents
    2. Retrieve relevant documents
    3. Generate answer using LLM
    4. Format and return response with metrics

    Usage:
        service = RAGService(collection_name="my_docs")
        metrics = service.initialize_from_documents(documents)
        response = service.answer_question("What is AI?", query_type="research")
        print(f"{response.answer}")
        print(f"Sources: {', '.join(response.sources)}")
    """

    def __init__(self, collection_name: str = "rag_documents"):
        """
        Initialize RAG service.

        Args:
            collection_name: Qdrant collection name
        """
        self.collection_name = collection_name
        self.pipeline_integrator = RAGPipelineIntegrator(
            collection_name=collection_name,
            use_metadata_extraction=True,
            force_recreate_collection=False,
        )
        self.chain_builder = None
        logger.info(f"RAGService initialized for collection: {collection_name}")

    def initialize_from_documents(
        self,
        documents: List[Document],
        force_recreate: bool = False,
    ) -> Dict[str, Any]:
        """
        Initialize RAG service with documents.

        Args:
            documents: List of Document objects
            force_recreate: Force recreation of collection

        Returns:
            Dictionary with initialization metrics

        Usage:
            from langchain_core.documents import Document
            docs = [Document(page_content="...", metadata={"source": "..."})]
            metrics = service.initialize_from_documents(docs)
            print(f"Indexed {metrics['total_vectors']} vectors")
        """
        logger.info(f"Initializing RAG service with {len(documents)} documents")

        self.pipeline_integrator.force_recreate_collection = force_recreate

        # Process documents through pipeline
        pipeline_metrics = self.pipeline_integrator.process_documents(documents)

        # Initialize chain builder with retriever
        retriever = self.pipeline_integrator.get_retriever(query_type="general")
        self.chain_builder = RAGChainBuilder(retriever)

        logger.info(f"RAG service initialized: {pipeline_metrics.total_vectors} vectors indexed")

        return {
            "total_documents": pipeline_metrics.total_documents,
            "total_chunks": pipeline_metrics.total_chunks,
            "total_vectors": pipeline_metrics.total_vectors,
            "collection_name": pipeline_metrics.collection_name,
            "processing_time_ms": pipeline_metrics.total_processing_time_ms,
            "estimated_cost_usd": pipeline_metrics.estimated_cost_usd,
        }

    def initialize_from_documents_with_progress(
        self,
        documents: List[Document],
        force_recreate: bool = False,
        upload_id: Optional[str] = None,
        progress_tracker = None,
    ) -> Dict[str, Any]:
        """
        Initialize RAG service with progress tracking.

        Args:
            documents: List of Document objects
            force_recreate: Force recreation of collection
            upload_id: Upload ID for progress tracking
            progress_tracker: ProgressTracker instance for sending updates

        Returns:
            Dictionary with initialization metrics
        """
        import asyncio
        from src.services.processing import ProcessingStatus

        logger.info(f"Initializing RAG service with {len(documents)} documents (upload: {upload_id})")

        self.pipeline_integrator.force_recreate_collection = force_recreate

        # Get event loop for async operations
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Process documents through pipeline
        # Note: Pipeline integrator will send progress updates
        pipeline_metrics = self.pipeline_integrator.process_documents(documents)

        # Initialize chain builder with retriever
        retriever = self.pipeline_integrator.get_retriever(query_type="general")
        self.chain_builder = RAGChainBuilder(retriever)

        logger.info(f"RAG service initialized: {pipeline_metrics.total_vectors} vectors indexed")

        return {
            "total_documents": pipeline_metrics.total_documents,
            "total_chunks": pipeline_metrics.total_chunks,
            "total_vectors": pipeline_metrics.total_vectors,
            "collection_name": pipeline_metrics.collection_name,
            "processing_time_ms": pipeline_metrics.total_processing_time_ms,
            "estimated_cost_usd": pipeline_metrics.estimated_cost_usd,
        }

    def answer_question(
        self,
        question: str,
        query_type: str = "general",
        k: int = 5,
    ) -> RAGResponse:
        """
        Answer a question using RAG.

        Args:
            question: User question
            query_type: Type of query (general, research, specific, complex)
            k: Number of documents to retrieve

        Returns:
            RAGResponse with answer and metrics

        Usage:
            response = service.answer_question(
                "What is deep learning?",
                query_type="research",
                k=5
            )
            print(f"{response.answer}")
            print(f"Retrieved {response.documents_used} documents in {response.retrieval_time_ms}ms")
        """
        if not self.chain_builder:
            raise RuntimeError("Service not initialized. Call initialize_from_documents() first.")

        logger.info(f"Answering question: {question[:100]}... (type: {query_type})")

        start_time = time.time()

        # Get retriever for this query type
        retrieval_start = time.time()
        retriever = self.pipeline_integrator.get_retriever(
            query_type=query_type,
            k=k,
        )
        retrieval_time_ms = (time.time() - retrieval_start) * 1000

        # Retrieve documents
        docs_start = time.time()
        retrieved_docs = retriever.invoke(question)
        docs_time_ms = (time.time() - docs_start) * 1000
        retrieval_time_ms += docs_time_ms

        # Build and invoke chain
        generation_start = time.time()
        chain = self.chain_builder.build_chain(query_type=query_type)

        # Get response
        response = chain.invoke(question)

        generation_time_ms = (time.time() - generation_start) * 1000

        # Extract text from response
        if hasattr(response, 'content'):
            answer_text = response.content
        else:
            answer_text = str(response)

        # Get sources
        sources = [doc.metadata.get("source", "unknown") for doc in retrieved_docs]

        total_time_ms = (time.time() - start_time) * 1000

        rag_response = RAGResponse(
            answer=answer_text,
            query_type=query_type,
            documents_used=len(retrieved_docs),
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            total_time_ms=total_time_ms,
            sources=sources,
            model=settings.openai_model,
        )

        logger.info(
            f"Question answered in {total_time_ms:.0f}ms "
            f"(retrieval: {retrieval_time_ms:.0f}ms, generation: {generation_time_ms:.0f}ms)"
        )

        return rag_response

    def batch_answer_questions(
        self,
        questions: List[str],
        query_type: str = "general",
        k: int = 5,
    ) -> List[RAGResponse]:
        """
        Answer multiple questions in batch.

        Args:
            questions: List of questions
            query_type: Type of queries
            k: Number of documents per query

        Returns:
            List of RAGResponse objects

        Usage:
            questions = [
                "What is machine learning?",
                "What is deep learning?",
                "What is NLP?"
            ]
            responses = service.batch_answer_questions(
                questions,
                query_type="research"
            )
            for response in responses:
                print(f"Q: {response}")
        """
        logger.info(f"Answering {len(questions)} questions in batch")

        responses = []
        for question in questions:
            response = self.answer_question(question, query_type=query_type, k=k)
            responses.append(response)

        logger.info(f"Batch complete: {len(responses)} questions answered")
        return responses

    def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get health status of RAG pipeline.

        Returns:
            Health status dictionary
        """
        return self.pipeline_integrator.get_pipeline_health()

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            Collection stats dictionary
        """
        return self.pipeline_integrator.get_collection_stats()

    def delete_collection(self) -> bool:
        """
        Delete the collection.

        Returns:
            True if successful
        """
        return self.pipeline_integrator.delete_collection()

    def search_documents(
        self,
        query: str,
        k: int = 5,
        query_type: str = "general",
    ) -> List[Document]:
        """
        Search for documents without generating answer.

        Args:
            query: Search query
            k: Number of results
            query_type: Type of retrieval strategy

        Returns:
            List of retrieved documents

        Usage:
            docs = service.search_documents("machine learning algorithms", k=3)
            for doc in docs:
                print(f"Source: {doc.metadata['source']}")
                print(f"Content: {doc.page_content[:100]}...")
        """
        retriever = self.pipeline_integrator.get_retriever(
            query_type=query_type,
            k=k,
        )
        return retriever.invoke(query)
