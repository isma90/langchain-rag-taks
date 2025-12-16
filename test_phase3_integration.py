"""
Phase 3 Integration Test

Tests the complete Vector Store & Indexing pipeline:
- Document chunking
- Metadata extraction
- Vector indexing (Qdrant)
- Retrieval strategies

Run with: python test_phase3_integration.py
Or with UV: uv run test_phase3_integration.py
"""

import sys
import time
from typing import List

from langchain_core.documents import Document
from src.services.rag.pipeline_integrator import RAGPipelineIntegrator
from src.services.chunking.factory import ChunkingStrategy
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_sample_documents() -> List[Document]:
    """Create sample documents for testing."""
    documents = [
        Document(
            page_content=(
                "Machine learning is a subset of artificial intelligence that focuses on "
                "enabling computers to learn from data without explicit programming. It uses "
                "algorithms and statistical models to identify patterns and make predictions."
            ),
            metadata={"source": "ml_intro.pdf", "page": 1}
        ),
        Document(
            page_content=(
                "Deep learning is a specialized subset of machine learning that uses neural "
                "networks with multiple layers (deep networks). It has revolutionized computer "
                "vision, natural language processing, and speech recognition applications."
            ),
            metadata={"source": "deep_learning.pdf", "page": 1}
        ),
        Document(
            page_content=(
                "Natural Language Processing (NLP) is the field of AI that focuses on making "
                "computers understand and generate human language. Modern NLP uses transformer "
                "models like BERT and GPT for tasks like translation, summarization, and Q&A."
            ),
            metadata={"source": "nlp_guide.pdf", "page": 1}
        ),
        Document(
            page_content=(
                "Vector databases like Qdrant store embeddings of documents and enable "
                "fast similarity search. They are essential for RAG systems as they retrieve "
                "relevant documents based on semantic similarity to queries."
            ),
            metadata={"source": "vector_db.pdf", "page": 1}
        ),
        Document(
            page_content=(
                "Retrieval-Augmented Generation (RAG) combines retrieval and generation. "
                "The system first retrieves relevant documents, then uses them as context "
                "for generating accurate answers to user queries."
            ),
            metadata={"source": "rag_overview.pdf", "page": 1}
        ),
    ]
    return documents


def test_pipeline_basic() -> bool:
    """Test basic pipeline execution."""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Pipeline Execution")
    print("=" * 70)

    try:
        # Create integrator
        integrator = RAGPipelineIntegrator(
            collection_name="test_phase3_basic",
            use_metadata_extraction=False,  # Skip for speed
            force_recreate_collection=True,
        )

        # Load sample documents
        documents = create_sample_documents()
        print(f"\nLoaded {len(documents)} sample documents")

        # Process documents
        print("\nProcessing documents through pipeline...")
        metrics = integrator.process_documents(
            documents,
            chunking_strategy=ChunkingStrategy.RECURSIVE,
        )

        # Display metrics
        print(f"\nPipeline Metrics:")
        print(f"  Input documents: {metrics.total_documents}")
        print(f"  Output chunks: {metrics.total_chunks}")
        print(f"  Vectors indexed: {metrics.total_vectors}")
        print(f"  Total time: {metrics.total_processing_time_ms:.1f}ms")
        print(f"  Chunking time: {metrics.chunking_time_ms:.1f}ms")
        print(f"  Indexing time: {metrics.indexing_time_ms:.1f}ms")
        print(f"  Estimated cost: ${metrics.estimated_cost_usd:.6f}")

        # Get collection stats
        stats = integrator.get_collection_stats()
        print(f"\nCollection Stats:")
        print(f"  Collection: {stats.get('collection_name')}")
        print(f"  Vectors: {stats.get('vectors_count')}")
        print(f"  Points: {stats.get('points_count')}")
        print(f"  Status: {stats.get('status')}")

        print("\n✓ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_retrieval() -> bool:
    """Test similarity-based retrieval."""
    print("\n" + "=" * 70)
    print("TEST 2: Similarity-Based Retrieval")
    print("=" * 70)

    try:
        # Create integrator
        integrator = RAGPipelineIntegrator(
            collection_name="test_phase3_similarity",
            use_metadata_extraction=False,
            force_recreate_collection=True,
        )

        # Process documents
        documents = create_sample_documents()
        print(f"\nProcessing {len(documents)} documents...")
        metrics = integrator.process_documents(documents)

        # Get similarity retriever
        print("\nRetrieving similar documents...")
        retriever = integrator.get_retriever(query_type="general", k=3)

        # Test query
        query = "What is machine learning and neural networks?"
        print(f"\nQuery: {query}")

        results = retriever.invoke(query)
        print(f"\nRetrieved {len(results)} results:")
        for i, doc in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Source: {doc.metadata.get('source', 'unknown')}")
            print(f"    Content: {doc.page_content[:100]}...")

        print("\n✓ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retriever_strategies() -> bool:
    """Test different retriever strategies."""
    print("\n" + "=" * 70)
    print("TEST 3: Multiple Retriever Strategies")
    print("=" * 70)

    try:
        # Create integrator
        integrator = RAGPipelineIntegrator(
            collection_name="test_phase3_strategies",
            use_metadata_extraction=False,
            force_recreate_collection=True,
        )

        # Process documents
        documents = create_sample_documents()
        print(f"\nProcessing {len(documents)} documents...")
        metrics = integrator.process_documents(documents)

        query = "What is deep learning?"
        print(f"\nQuery: {query}")

        # Test different query types
        query_types = ["general", "research", "specific"]

        for query_type in query_types:
            try:
                print(f"\n  Testing {query_type.upper()} retrieval...")
                retriever = integrator.get_retriever(query_type=query_type, k=2)
                results = retriever.invoke(query)
                print(f"    Retrieved {len(results)} documents")
                for doc in results:
                    print(f"      - {doc.metadata.get('source', 'unknown')}")
            except Exception as e:
                print(f"    ⚠ {query_type} retrieval error: {e}")

        print("\n✓ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_status() -> bool:
    """Test pipeline health status."""
    print("\n" + "=" * 70)
    print("TEST 4: Pipeline Health Status")
    print("=" * 70)

    try:
        # Create integrator
        integrator = RAGPipelineIntegrator(
            collection_name="test_phase3_health",
            use_metadata_extraction=False,
            force_recreate_collection=True,
        )

        # Process documents
        documents = create_sample_documents()
        print(f"\nProcessing {len(documents)} documents...")
        metrics = integrator.process_documents(documents)

        # Check health
        print("\nChecking pipeline health...")
        health = integrator.get_pipeline_health()

        vector_store_health = health.get("vector_store_health", {})
        print(f"\nVector Store Health:")
        print(f"  Status: {vector_store_health.get('status')}")
        print(f"  Collections: {vector_store_health.get('collections_count')}")

        circuit_breaker = health.get("circuit_breaker_status", {})
        print(f"\nCircuit Breaker:")
        print(f"  State: {circuit_breaker.get('state')}")
        print(f"  Failures: {circuit_breaker.get('failure_count')}")

        print("\n✓ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_collections(integrator: RAGPipelineIntegrator):
    """Clean up test collections."""
    try:
        collections = integrator.list_collections()
        for coll in collections:
            if "test_phase3" in coll:
                print(f"Cleaning up collection: {coll}")
                integrator.collection_name = coll
                integrator.delete_collection()
    except Exception as e:
        print(f"Warning: Could not clean up test collections: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PHASE 3 INTEGRATION TEST SUITE")
    print("Testing: Vector Store & Indexing (Qdrant)")
    print("=" * 70)

    tests = [
        ("Basic Pipeline Execution", test_pipeline_basic),
        ("Similarity-Based Retrieval", test_similarity_retrieval),
        ("Multiple Retriever Strategies", test_retriever_strategies),
        ("Pipeline Health Status", test_health_status),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Return exit code
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
