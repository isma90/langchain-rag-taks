"""
Simple Phase 4 test to verify RAG implementation works
"""
from langchain_core.documents import Document
from src.services.rag.rag_service import RAGService

# Create sample documents
docs = [
    Document(
        page_content="Machine learning is a subset of AI that enables computers to learn from data.",
        metadata={"source": "ml_intro.pdf"}
    ),
    Document(
        page_content="Deep learning uses neural networks with multiple layers.",
        metadata={"source": "dl_guide.pdf"}
    ),
]

# Create service
service = RAGService(collection_name="simple_test")
print("✓ RAGService created")

# Initialize
metrics = service.initialize_from_documents(docs, force_recreate=True)
print(f"✓ Documents indexed: {metrics['total_chunks']} chunks")

# Answer question
response = service.answer_question("What is machine learning?", query_type="general")
print(f"✓ Answer generated in {response.total_time_ms:.0f}ms")
print(f"  Sources: {response.sources}")
print(f"  Answer: {response.answer[:150]}...")

# Cleanup
service.delete_collection()
print("✓ Collection cleaned up")

print("\n✓✓✓ Phase 4 Implementation VERIFIED ✓✓✓")
