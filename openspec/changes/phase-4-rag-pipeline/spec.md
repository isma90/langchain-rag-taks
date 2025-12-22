# Phase 4: Basic RAG Pipeline - Specification

**Change ID**: `phase-4-rag-pipeline`
**Version**: 1.0
**Status**: IMPLEMENTED

## RAG Pipeline Orchestration Capability

### ADDED Requirements

#### Requirement: RAGPipelineIntegrator

Central orchestrator for the complete RAG pipeline.

**Specification**:
- Responsibilities:
  1. Document chunking (via ChunkingFactory)
  2. Metadata enrichment (via MetadataHandler)
  3. Vector indexing (via QdrantVectorStoreManager)
  4. Retriever creation
  5. Health monitoring
- Input: Raw documents
- Output: PipelineMetrics with processing details
- Supports: Multiple chunking strategies, optional metadata extraction
- Error Handling: Graceful degradation, detailed error logging

**Methods**:
- `process_documents(documents, chunking_strategy, enable_metadata)` → PipelineMetrics
- `get_retriever(query_type, k)` → BaseRetriever
- `get_pipeline_health()` → Health status dict
- `get_collection_stats()` → Collection statistics
- `delete_collection()` → Boolean success

**Scenarios**:
1. Load 100 documents → Chunk → Extract metadata → Index
2. Track processing time, vector count, costs
3. Get retriever for specific query type
4. Monitor health of pipeline components
5. Clean up collections

**File**: `src/services/rag/pipeline_integrator.py`

#### Requirement: PipelineMetrics Dataclass

Track metrics from pipeline execution.

**Specification**:
- Fields:
  - `total_documents` - Original document count
  - `total_chunks` - Resulting chunks after splitting
  - `total_vectors` - Vectors indexed in Qdrant
  - `collection_name` - Qdrant collection name
  - `total_processing_time_ms` - Total time in milliseconds
  - `estimated_cost_usd` - Estimated API costs
- Used for monitoring and reporting

---

## LCEL Chain Building Capability

### ADDED Requirement: RAGChainBuilder

Factory for creating LCEL chains with specialized prompts.

**Specification**:
- Class: `RAGChainBuilder`
- Input: Retriever + optional LLM (defaults to gpt-4o)
- Methods:
  - `build_chain(query_type)` → LCEL Runnable
  - `build_general_chain()` → Direct Q&A chain
  - `build_research_chain()` → Detailed analysis chain
  - `build_specific_chain()` → Domain-specific chain
  - `build_complex_chain()` → Multi-step reasoning chain

- Chain Structure:
  ```
  {context: retriever | format_docs, question: passthrough}
  | prompt_template
  | llm
  ```

**Scenarios**:
1. Create general chain for simple questions
2. Create research chain for comparative analysis
3. Create specific chain for technical questions
4. Create complex chain for synthesis tasks

**File**: `src/services/rag/chain_builder.py`

---

## Query Type Specific Prompts

### ADDED Requirements

#### Requirement: General Query Prompt

Simple, direct question-answering prompt.

**Specification**:
- Purpose: Quick answers to straightforward questions
- Tone: Clear, concise, direct
- Context: Basic document context
- Output: Single focused answer

**Prompt Template**:
```
System: You are a helpful assistant that answers questions based on provided documents.
Provide clear, concise answers directly addressing the user's question.
If the answer isn't in the documents, say so clearly.```

#### Requirement: Research Query Prompt

Detailed, source-aware prompt for research-style questions.

**Specification**:
- Purpose: Comprehensive answers with multiple perspectives
- Tone: Academic, detailed, comparative
- Context: All relevant documents with citations
- Output: Structured answer with sources and analysis

#### Requirement: Specific Domain Prompt

Technical, domain-specific prompt.

**Specification**:
- Purpose: Specialized answers for technical questions
- Tone: Expert, technical, practical
- Context: Domain-specific documents
- Output: Technical answer with specific references

#### Requirement: Complex Multi-Step Prompt

Advanced reasoning prompt for synthesis.

**Specification**:
- Purpose: Multi-step analysis and synthesis
- Tone: Analytical, structured, reasoning-focused
- Context: All relevant documents
- Output: Step-by-step reasoning with conclusions

---

## RAG Service Capability

### ADDED Requirement: High-Level RAGService

End-to-end question-answering service.

**Specification**:
- Class: `RAGService`
- Constructor: Takes collection_name
- Key Methods:
  - `initialize_from_documents(documents, force_recreate)` → Initialization metrics
  - `answer_question(question, query_type, k)` → RAGResponse
  - `batch_answer_questions(questions, query_type, k)` → List[RAGResponse]
  - `search_documents(query, k, query_type)` → List[Document]
  - `get_pipeline_health()` → Health status
  - `get_collection_stats()` → Collection stats
  - `delete_collection()` → Boolean

**Scenarios**:
1. Initialize: Load documents
2. Query: Ask question, get structured response
3. Batch: Process multiple questions efficiently
4. Search: Find documents without generating answer
5. Monitor: Check pipeline health
6. Cleanup: Remove collection

**File**: `src/services/rag/rag_service.py`

#### Requirement: RAGResponse Dataclass

Structured response from question answering.

**Specification**:
- Fields:
  - `answer` - Generated answer text
  - `query_type` - Type of query used
  - `documents_used` - Count of retrieved documents
  - `retrieval_time_ms` - Time to retrieve documents
  - `generation_time_ms` - Time for LLM generation
  - `total_time_ms` - Total end-to-end time
  - `sources` - List of source documents
  - `model` - LLM model name used

**Usage**: Structured response for APIs and logging

---

## Integration Points

**Phase 2** (Chunking):
- Uses: ChunkingFactory for document splitting
- Tracks: Chunk count in metrics

**Phase 3** (Vector Store):
- Uses: RetrieverFactory for document retrieval
- Uses: Metadata for context enrichment

**Phase 5** (Deployment):
- Exposed: via FastAPI endpoints
- Called by: API /question endpoint

---

## Architecture & Patterns

### Pipeline Orchestration Pattern
- **Class**: RAGPipelineIntegrator
- **Pattern**: Orchestrator for complex workflows
- **Benefit**: Manages multiple sub-systems

### Chain Builder Pattern
- **Class**: RAGChainBuilder
- **Pattern**: Factory for composable chains
- **Benefit**: Easy to add new prompt types

### Service Layer Pattern
- **Class**: RAGService
- **Pattern**: High-level API over pipeline
- **Benefit**: Clean separation of concerns

---

## Dependencies

```
langchain >= 0.1.0
langchain-openai >= 0.1.0
langchain-qdrant >= 1.1.0
```

---

## Testing

- [x] test_rag_service_initialization - Service setup
- [x] test_general_query_answering - General chain
- [x] test_research_query_answering - Research chain
- [x] test_specific_query_answering - Specific chain
- [x] test_complex_query_answering - Complex chain
- [x] test_batch_answering - Batch processing
- [x] test_document_search - Search without generation
- [x] test_pipeline_health - Health checks
- Result: **8/8 tests passing** ✓

---

## Status

- [x] Design approved
- [x] Implementation complete
- [x] Tests passing (8/8)
- [x] Integrated with Phase 2, 3, 5
- [x] Documentation complete
- [x] Production ready

**Completed**: December 22, 2025
