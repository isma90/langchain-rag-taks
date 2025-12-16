"""
Phase 4 Integration Test

Tests the complete RAG pipeline:
- LCEL chain building
- Question answering with multiple query types
- RAG service integration
- Response formatting and metrics

Run with: python test_phase4_integration.py
Or with UV: uv run test_phase4_integration.py
"""

import sys
import time
from typing import List

from langchain_core.documents import Document
from src.services.rag.rag_service import RAGService, RAGResponse
from src.services.rag.chain_builder import QueryType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_sample_documents() -> List[Document]:
    """Create sample documents for testing."""
    documents = [
        Document(
            page_content=(
                "Machine learning is a subset of artificial intelligence that focuses on "
                "enabling computers to learn from data without explicit programming. It uses "
                "algorithms and statistical models to identify patterns and make predictions. "
                "Common techniques include supervised learning, unsupervised learning, and reinforcement learning."
            ),
            metadata={"source": "ml_intro.pdf", "page": 1, "topic": "machine-learning"}
        ),
        Document(
            page_content=(
                "Deep learning is a specialized subset of machine learning that uses neural "
                "networks with multiple layers (deep networks). It has revolutionized computer "
                "vision, natural language processing, and speech recognition applications. "
                "Convolutional Neural Networks (CNNs) excel at image processing while Recurrent Neural "
                "Networks (RNNs) are used for sequential data."
            ),
            metadata={"source": "deep_learning.pdf", "page": 1, "topic": "deep-learning"}
        ),
        Document(
            page_content=(
                "Natural Language Processing (NLP) is the field of AI that focuses on making "
                "computers understand and generate human language. Modern NLP uses transformer "
                "models like BERT and GPT for tasks like translation, summarization, and Q&A. "
                "The attention mechanism is a key innovation that allows models to focus on "
                "relevant parts of input when generating output."
            ),
            metadata={"source": "nlp_guide.pdf", "page": 1, "topic": "nlp"}
        ),
        Document(
            page_content=(
                "Vector databases like Qdrant store embeddings of documents and enable "
                "fast similarity search. They are essential for RAG systems as they retrieve "
                "relevant documents based on semantic similarity to queries. Embeddings are "
                "high-dimensional representations of text that capture semantic meaning. "
                "Distance metrics like cosine similarity measure how close embeddings are."
            ),
            metadata={"source": "vector_db.pdf", "page": 1, "topic": "databases"}
        ),
        Document(
            page_content=(
                "Retrieval-Augmented Generation (RAG) combines retrieval and generation. "
                "The system first retrieves relevant documents, then uses them as context "
                "for generating accurate answers to user queries. This approach improves "
                "answer quality by grounding responses in actual source material. RAG systems "
                "can be more reliable than pure language models for factual questions."
            ),
            metadata={"source": "rag_overview.pdf", "page": 1, "topic": "rag"}
        ),
        Document(
            page_content=(
                "Transformer models are the foundation of modern NLP. They use self-attention "
                "mechanisms to process input sequences in parallel rather than sequentially. "
                "GPT (Generative Pre-trained Transformer) models are trained on massive amounts "
                "of text data and can be fine-tuned for specific tasks. BERT (Bidirectional Encoder "
                "Representations from Transformers) provides strong representations for understanding tasks."
            ),
            metadata={"source": "transformers.pdf", "page": 1, "topic": "nlp"}
        ),
    ]
    return documents


def test_rag_service_initialization() -> bool:
    """Test RAG service initialization with documents."""
    print("\n" + "=" * 70)
    print("TEST 1: RAG Service Initialization")
    print("=" * 70)

    try:
        # Create service
        service = RAGService(collection_name="test_phase4_basic")
        print(f"\nRAG Service created for collection: test_phase4_basic")

        # Create sample documents
        documents = create_sample_documents()
        print(f"Created {len(documents)} sample documents")

        # Initialize with documents
        print("\nInitializing service with documents...")
        metrics = service.initialize_from_documents(
            documents,
            force_recreate=True,
        )

        print(f"\nInitialization Metrics:")
        print(f"  Total documents: {metrics['total_documents']}")
        print(f"  Total chunks: {metrics['total_chunks']}")
        print(f"  Total vectors: {metrics['total_vectors']}")
        print(f"  Processing time: {metrics['processing_time_ms']:.1f}ms")
        print(f"  Estimated cost: ${metrics['estimated_cost_usd']:.6f}")

        print("\n✓ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_general_query_answering() -> bool:
    """Test basic question answering."""
    print("\n" + "=" * 70)
    print("TEST 2: General Query Answering")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_general")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Ask general question
        question = "What is machine learning?"
        print(f"\nQuestion: {question}")
        print(f"Query Type: GENERAL")

        response = service.answer_question(
            question=question,
            query_type="general",
            k=3,
        )

        print(f"\nResponse:")
        print(f"  Answer: {response.answer[:200]}...")
        print(f"\nMetrics:")
        print(f"  Documents used: {response.documents_used}")
        print(f"  Sources: {', '.join(response.sources)}")
        print(f"  Retrieval time: {response.retrieval_time_ms:.1f}ms")
        print(f"  Generation time: {response.generation_time_ms:.1f}ms")
        print(f"  Total time: {response.total_time_ms:.1f}ms")
        print(f"  Model: {response.model}")

        assert response.documents_used > 0, "Should have retrieved documents"
        assert len(response.answer) > 0, "Should have generated answer"
        assert response.total_time_ms > 0, "Should have timing metrics"

        print("\n✓ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_research_query_answering() -> bool:
    """Test research-focused question answering."""
    print("\n" + "=" * 70)
    print("TEST 3: Research Query Answering")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_research")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Ask research question
        question = "Compare deep learning and traditional machine learning approaches."
        print(f"\nQuestion: {question}")
        print(f"Query Type: RESEARCH")

        response = service.answer_question(
            question=question,
            query_type="research",
            k=5,
        )

        print(f"\nResponse:")
        print(f"  Answer (first 300 chars): {response.answer[:300]}...")
        print(f"\nMetrics:")
        print(f"  Documents used: {response.documents_used}")
        print(f"  Sources: {', '.join(response.sources)}")
        print(f"  Retrieval time: {response.retrieval_time_ms:.1f}ms")
        print(f"  Generation time: {response.generation_time_ms:.1f}ms")
        print(f"  Total time: {response.total_time_ms:.1f}ms")

        assert response.documents_used > 0, "Should have retrieved documents"
        assert len(response.answer) > 0, "Should have generated detailed answer"

        print("\n✓ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_query_answering() -> bool:
    """Test domain-specific question answering."""
    print("\n" + "=" * 70)
    print("TEST 4: Specific Query Answering")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_specific")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Ask specific question
        question = "What are transformers and how do they work?"
        print(f"\nQuestion: {question}")
        print(f"Query Type: SPECIFIC")

        response = service.answer_question(
            question=question,
            query_type="specific",
            k=3,
        )

        print(f"\nResponse:")
        print(f"  Answer (first 250 chars): {response.answer[:250]}...")
        print(f"\nMetrics:")
        print(f"  Documents used: {response.documents_used}")
        print(f"  Sources: {', '.join(response.sources)}")
        print(f"  Retrieval time: {response.retrieval_time_ms:.1f}ms")
        print(f"  Generation time: {response.generation_time_ms:.1f}ms")
        print(f"  Total time: {response.total_time_ms:.1f}ms")

        assert response.documents_used > 0, "Should have retrieved documents"
        assert len(response.answer) > 0, "Should have generated focused answer"

        print("\n✓ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_query_answering() -> bool:
    """Test complex multi-step question answering."""
    print("\n" + "=" * 70)
    print("TEST 5: Complex Query Answering")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_complex")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Ask complex question
        question = "Explain the relationship between embeddings, transformers, and RAG systems in modern NLP applications."
        print(f"\nQuestion: {question}")
        print(f"Query Type: COMPLEX")

        response = service.answer_question(
            question=question,
            query_type="complex",
            k=5,
        )

        print(f"\nResponse:")
        print(f"  Answer (first 300 chars): {response.answer[:300]}...")
        print(f"\nMetrics:")
        print(f"  Documents used: {response.documents_used}")
        print(f"  Sources: {', '.join(response.sources)}")
        print(f"  Retrieval time: {response.retrieval_time_ms:.1f}ms")
        print(f"  Generation time: {response.generation_time_ms:.1f}ms")
        print(f"  Total time: {response.total_time_ms:.1f}ms")

        assert response.documents_used > 0, "Should have retrieved documents"
        assert len(response.answer) > 0, "Should have generated comprehensive answer"

        print("\n✓ TEST 5 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_answering() -> bool:
    """Test answering multiple questions."""
    print("\n" + "=" * 70)
    print("TEST 6: Batch Question Answering")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_batch")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Batch questions
        questions = [
            "What is machine learning?",
            "What are transformers?",
            "How does RAG work?"
        ]
        print(f"\nAnswering {len(questions)} questions in batch...")

        responses = service.batch_answer_questions(
            questions=questions,
            query_type="general",
            k=3,
        )

        print(f"\nBatch Results:")
        total_time = 0
        for i, response in enumerate(responses, 1):
            print(f"\n  Question {i}: {questions[i-1][:50]}...")
            print(f"    Documents used: {response.documents_used}")
            print(f"    Time: {response.total_time_ms:.1f}ms")
            total_time += response.total_time_ms

        print(f"\n  Total batch time: {total_time:.1f}ms")
        print(f"  Average time per question: {total_time/len(questions):.1f}ms")

        assert len(responses) == len(questions), "Should have response for each question"
        for response in responses:
            assert len(response.answer) > 0, "Each response should have content"

        print("\n✓ TEST 6 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_search() -> bool:
    """Test document search without answer generation."""
    print("\n" + "=" * 70)
    print("TEST 7: Document Search")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_search")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Search documents
        query = "neural networks and deep learning"
        print(f"\nSearch Query: {query}")

        docs = service.search_documents(query=query, k=3, query_type="general")

        print(f"\nFound {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            topic = doc.metadata.get("topic", "unknown")
            print(f"\n  Document {i}:")
            print(f"    Source: {source}")
            print(f"    Topic: {topic}")
            print(f"    Content: {doc.page_content[:100]}...")

        assert len(docs) > 0, "Should have found documents"

        print("\n✓ TEST 7 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 7 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_health() -> bool:
    """Test pipeline health status."""
    print("\n" + "=" * 70)
    print("TEST 8: Pipeline Health Status")
    print("=" * 70)

    try:
        # Create and initialize service
        service = RAGService(collection_name="test_phase4_health")
        documents = create_sample_documents()
        service.initialize_from_documents(documents, force_recreate=True)

        # Check health
        print("\nChecking pipeline health...")
        health = service.get_pipeline_health()

        vector_store = health.get("vector_store_health", {})
        print(f"\nVector Store Health:")
        print(f"  Status: {vector_store.get('status')}")
        print(f"  Collections: {vector_store.get('collections_count')}")

        circuit_breaker = health.get("circuit_breaker_status", {})
        print(f"\nCircuit Breaker:")
        print(f"  State: {circuit_breaker.get('state')}")
        print(f"  Failures: {circuit_breaker.get('failure_count')}")

        stats = service.get_collection_stats()
        print(f"\nCollection Stats:")
        print(f"  Vectors: {stats.get('vectors_count')}")
        print(f"  Points: {stats.get('points_count')}")
        print(f"  Status: {stats.get('status')}")

        assert vector_store.get('status') == 'healthy', "Vector store should be healthy"

        print("\n✓ TEST 8 PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TEST 8 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_collections():
    """Clean up test collections."""
    try:
        service = RAGService(collection_name="test_phase4_basic")
        # Try to delete each test collection
        for suffix in ["basic", "general", "research", "specific", "complex", "batch", "search", "health"]:
            service.collection_name = f"test_phase4_{suffix}"
            try:
                service.delete_collection()
                print(f"Cleaned up collection: test_phase4_{suffix}")
            except Exception:
                pass
    except Exception as e:
        print(f"Warning: Could not clean up test collections: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PHASE 4 INTEGRATION TEST SUITE")
    print("Testing: RAG Pipeline with LCEL Chains")
    print("=" * 70)

    tests = [
        ("RAG Service Initialization", test_rag_service_initialization),
        ("General Query Answering", test_general_query_answering),
        ("Research Query Answering", test_research_query_answering),
        ("Specific Query Answering", test_specific_query_answering),
        ("Complex Query Answering", test_complex_query_answering),
        ("Batch Question Answering", test_batch_answering),
        ("Document Search", test_document_search),
        ("Pipeline Health Status", test_pipeline_health),
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

    # Cleanup
    print("\nCleaning up test collections...")
    cleanup_test_collections()

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
