"""
FastAPI RAG API

Production-ready REST API for RAG pipeline
Includes automatic rate limiting to stay within OpenAI's 3,500 RPM tier.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import time
import uuid
import json
import asyncio

from src.services.rag.rag_service import RAGService, RAGResponse
from src.config.settings import settings
from src.utils.logging_config import get_logger
from src.services.rate_limiting import add_rate_limit_middleware, get_rate_limiter
from src.services.processing import get_progress_tracker, ProcessingStatus

logger = get_logger(__name__)

# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentInput(BaseModel):
    """Document input model"""
    content: str = Field(..., description="Document content")
    source: str = Field(default="unknown", description="Document source")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class InitializeRequest(BaseModel):
    """Initialize RAG service request"""
    collection_name: str = Field(default="rag_documents", description="Collection name")
    documents: List[DocumentInput] = Field(..., description="Documents to index")
    force_recreate: bool = Field(default=False, description="Force recreate collection")


class QuestionRequest(BaseModel):
    """Question answering request"""
    question: str = Field(..., description="User question")
    query_type: str = Field(default="general", description="Query type: general, research, specific, complex")
    k: int = Field(default=5, description="Number of documents to retrieve")


class SearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, description="Number of results")
    query_type: str = Field(default="general", description="Search strategy type")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    timestamp: float


class InitializeResponse(BaseModel):
    """Initialize response"""
    status: str
    total_documents: int
    total_chunks: int
    total_vectors: int
    processing_time_ms: float
    estimated_cost_usd: float


class AnswerResponse(BaseModel):
    """Answer response"""
    answer: str
    query_type: str
    documents_used: int
    sources: List[str]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    model: str


class SearchResponse(BaseModel):
    """Search response"""
    documents: List[dict]
    count: int
    search_time_ms: float


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: float


class UploadStartResponse(BaseModel):
    """Response when upload is received"""
    upload_id: str
    status: str
    message: str
    timestamp: float


class ProgressResponse(BaseModel):
    """Progress update response"""
    upload_id: str
    status: str
    progress_percent: float
    current_chunk: int
    total_chunks: int
    message: str
    timestamp: str


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="RAG API",
    description="Production-ready Retrieval-Augmented Generation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# Middleware
# ============================================================================

# Rate Limiting (Custom RPM limit)
add_rate_limit_middleware(app, max_rpm=10, adaptive=False)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Global state
# ============================================================================

_rag_service: Optional[RAGService] = None
_collection_name: str = "rag_documents"


def get_rag_service() -> RAGService:
    """Get or initialize RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(collection_name=_collection_name)
    return _rag_service


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.environment,
        timestamp=time.time()
    )


@app.post("/initialize", response_model=InitializeResponse)
async def initialize_rag(request: InitializeRequest):
    """
    Initialize RAG service with documents.

    This endpoint processes documents and indexes them in the vector database.
    """
    try:
        logger.info(f"Initializing RAG with {len(request.documents)} documents")

        # Convert input documents to LangChain format
        from langchain_core.documents import Document
        documents = [
            Document(
                page_content=doc.content,
                metadata={"source": doc.source, **(doc.metadata or {})}
            )
            for doc in request.documents
        ]

        # Initialize service
        global _collection_name
        _collection_name = request.collection_name

        service = RAGService(collection_name=request.collection_name)
        metrics = service.initialize_from_documents(
            documents,
            force_recreate=request.force_recreate
        )

        return InitializeResponse(
            status="success",
            total_documents=metrics["total_documents"],
            total_chunks=metrics["total_chunks"],
            total_vectors=metrics["total_vectors"],
            processing_time_ms=metrics["processing_time_ms"],
            estimated_cost_usd=metrics["estimated_cost_usd"]
        )

    except Exception as e:
        logger.error(f"Error initializing RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadStartResponse)
async def start_upload(request: InitializeRequest, background_tasks: BackgroundTasks):
    """
    Start document upload with background processing.

    Returns immediately with upload_id. Client should connect to WebSocket
    endpoint /ws/{upload_id} to receive progress updates.
    """
    try:
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())

        logger.info(f"Starting upload {upload_id} with {len(request.documents)} documents")

        # Convert input documents to LangChain format
        from langchain_core.documents import Document
        documents = [
            Document(
                page_content=doc.content,
                metadata={"source": doc.source, **(doc.metadata or {})}
            )
            for doc in request.documents
        ]

        # Initialize progress tracker
        progress_tracker = get_progress_tracker()

        # Estimate chunks (rough: ~3 chunks per document)
        estimated_chunks = max(len(documents) * 3, 1)
        await progress_tracker.start_upload(upload_id, estimated_chunks)

        # Schedule background processing
        background_tasks.add_task(
            _process_upload_background,
            upload_id,
            request.collection_name,
            documents,
            request.force_recreate,
        )

        return UploadStartResponse(
            upload_id=upload_id,
            status="received",
            message=f"Upload received. Total documents: {len(documents)}",
            timestamp=time.time()
        )

    except Exception as e:
        logger.error(f"Error starting upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{upload_id}")
async def websocket_progress(websocket: WebSocket, upload_id: str):
    """
    WebSocket endpoint for real-time progress updates.

    Clients connect with upload_id and receive progress messages as documents
    are processed.
    """
    await websocket.accept()

    try:
        progress_tracker = get_progress_tracker()

        logger.info(f"WebSocket client connected for upload {upload_id}")

        # Register callback for this upload
        async def send_progress(update):
            try:
                await websocket.send_json(update.to_dict())
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")

        progress_tracker.register_callback(upload_id, send_progress)

        # Keep connection alive and listen for any client messages
        # (client can send "close" to disconnect cleanly)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)
                if data == "close":
                    break
            except asyncio.TimeoutError:
                # Timeout after 5 minutes
                logger.warning(f"WebSocket timeout for upload {upload_id}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for upload {upload_id}")
    except Exception as e:
        logger.error(f"WebSocket error for upload {upload_id}: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


async def _process_upload_background(
    upload_id: str,
    collection_name: str,
    documents,
    force_recreate: bool,
):
    """
    Process upload in background and send progress updates.
    """
    progress_tracker = get_progress_tracker()

    try:
        logger.info(f"Starting background processing for upload {upload_id}")

        await progress_tracker.update_progress(
            upload_id,
            ProcessingStatus.EXTRACTING,
            0,
            "Extracting content from documents..."
        )

        # Initialize service
        global _collection_name
        _collection_name = collection_name

        service = RAGService(collection_name=collection_name)

        # Process with progress tracking
        metrics = await asyncio.to_thread(
            service.initialize_from_documents_with_progress,
            documents,
            force_recreate,
            upload_id,
            progress_tracker,
        )

        # Mark as completed
        await progress_tracker.complete_upload(upload_id)

        logger.info(f"Completed processing for upload {upload_id}")

    except Exception as e:
        logger.error(f"Error processing upload {upload_id}: {e}")
        await progress_tracker.fail_upload(upload_id, str(e))


@app.post("/question", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    """
    Answer a question using the RAG pipeline.
    Auto-initializes from Qdrant Cloud if service not already initialized.
    """
    try:
        logger.info(f"Answering question: {request.question[:100]}...")

        service = get_rag_service()

        # Check if service needs initialization
        try:
            # Try to answer the question directly
            response = service.answer_question(
                question=request.question,
                query_type=request.query_type,
                k=request.k
            )
            return AnswerResponse(
                answer=response.answer,
                query_type=response.query_type,
                documents_used=response.documents_used,
                sources=response.sources,
                retrieval_time_ms=response.retrieval_time_ms,
                generation_time_ms=response.generation_time_ms,
                total_time_ms=response.total_time_ms,
                model=response.model
            )
        except Exception as e:
            if "not initialized" in str(e).lower():
                # Auto-initialize from Qdrant Cloud
                logger.info("Service not initialized. Auto-initializing from Qdrant Cloud...")
                try:
                    # Initialize with a minimal document - this loads from Qdrant Cloud
                    from langchain_core.documents import Document
                    service.initialize_from_documents(
                        documents=[Document(
                            page_content="Auto-initializing from Qdrant Cloud collection",
                            metadata={"source": "qdrant_cloud"}
                        )],
                        force_recreate=False
                    )
                    logger.info("Auto-initialization from Qdrant Cloud completed")

                    # Now try the question again
                    response = service.answer_question(
                        question=request.question,
                        query_type=request.query_type,
                        k=request.k
                    )
                    return AnswerResponse(
                        answer=response.answer,
                        query_type=response.query_type,
                        documents_used=response.documents_used,
                        sources=response.sources,
                        retrieval_time_ms=response.retrieval_time_ms,
                        generation_time_ms=response.generation_time_ms,
                        total_time_ms=response.total_time_ms,
                        model=response.model
                    )
                except Exception as init_error:
                    logger.error(f"Auto-initialization failed: {init_error}")
                    raise HTTPException(
                        status_code=503,
                        detail=f"Service initialization failed. Please call /initialize first. Error: {str(init_error)}"
                    )
            else:
                # Some other error occurred
                raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search for documents without generating an answer.
    """
    try:
        logger.info(f"Searching documents: {request.query}")

        start = time.time()
        service = get_rag_service()
        docs = service.search_documents(
            query=request.query,
            k=request.k,
            query_type=request.query_type
        )
        search_time = (time.time() - start) * 1000

        documents = [
            {
                "content": doc.page_content[:200],
                "source": doc.metadata.get("source", "unknown"),
                "metadata": doc.metadata
            }
            for doc in docs
        ]

        return SearchResponse(
            documents=documents,
            count=len(documents),
            search_time_ms=search_time
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-questions")
async def batch_answer_questions(questions: List[str], query_type: str = "general"):
    """
    Answer multiple questions in batch.
    """
    try:
        logger.info(f"Answering {len(questions)} questions in batch")

        service = get_rag_service()
        responses = service.batch_answer_questions(
            questions=questions,
            query_type=query_type
        )

        return {
            "status": "success",
            "total_questions": len(questions),
            "answers": [
                {
                    "question": questions[i],
                    "answer": resp.answer,
                    "sources": resp.sources,
                    "time_ms": resp.total_time_ms
                }
                for i, resp in enumerate(responses)
            ]
        }

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get pipeline statistics.
    """
    try:
        service = get_rag_service()
        stats = service.get_collection_stats()
        health = service.get_pipeline_health()

        return {
            "status": "success",
            "collection_stats": stats,
            "pipeline_health": health,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rate-limit-stats")
async def get_rate_limit_stats():
    """
    Get OpenAI rate limiting statistics.

    Returns:
        - current_rpm: Current requests per minute
        - max_rpm: Maximum allowed requests per minute (3,500)
        - utilization_percent: Current utilization as percentage
        - services: Per-service request counts
    """
    try:
        rate_limiter = get_rate_limiter()
        stats = rate_limiter.get_stats()

        return {
            "status": "success",
            "rate_limiting": stats,
            "timestamp": time.time(),
            "info": {
                "max_rpm": 3500,
                "tier": "OpenAI Basic Tier",
                "description": "Automatic rate limiting to stay within OpenAI's 3,500 RPM limit"
            }
        }

    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """
    Delete a collection.
    """
    try:
        logger.info(f"Deleting collection: {collection_name}")

        service = RAGService(collection_name=collection_name)
        success = service.delete_collection()

        if success:
            return {"status": "success", "message": f"Collection '{collection_name}' deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete collection")

    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"RAG API starting up (environment: {settings.environment})")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Redis URL: {settings.redis_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("RAG API shutting down")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": time.time()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
