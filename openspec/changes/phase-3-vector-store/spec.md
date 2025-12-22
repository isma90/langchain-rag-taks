# Phase 3: Vector Store & Indexing - Specification

**Change ID**: `phase-3-vector-store`
**Version**: 1.0
**Status**: IMPLEMENTED

## Vector Database Integration Capability

### ADDED Requirements

#### Requirement: Qdrant Cloud Integration

Integration with Qdrant Cloud for vector storage and semantic search.

**Specification**:
- Provider: Qdrant Cloud (managed service)
- Endpoint: `https://<instance-id>.us-east4-0.gcp.cloud.qdrant.io`
- Authentication: API Key in .env (QDRANT_API_KEY)
- Vector Dimension: 512 (text-embedding-3-large)
- Collection Management: Create, delete, search collections
- Connection Pooling: Automatic retry + circuit breaker

**Scenarios**:
1. Create collection on first document load
2. Add 1000s of documents with embeddings
3. Search by semantic similarity
4. Handle connection failures gracefully
5. Monitor collection health

**Files**: `src/services/vector_store/qdrant_manager.py`

#### Requirement: QdrantVectorStoreManager

Manager class for Qdrant operations.

**Specification**:
- Methods:
  - `create_collection(name, vector_size)` - Create or recreate
  - `add_documents(collection, docs_with_embeddings)` - Batch indexing
  - `list_collections()` - Get all collections
  - `get_health_status()` - Health check
  - `create_retriever(collection, search_kwargs)` - Get retriever
  - `delete_collection(name)` - Remove collection
- Batch Size: 100 documents per API call
- Retry: 3 attempts with exponential backoff
- Circuit Breaker: Opens after 5 failures, timeout 60s

**Scenarios**:
1. Initialize collection with 1000 documents
2. Query for top-5 most similar vectors
3. Handle rate limiting with retries
4. Circuit opens on connection failure
5. Graceful degradation

---

## Embedding Generation Capability

### ADDED Requirement: OpenAI Embeddings Service

Generate embeddings using OpenAI's API.

**Specification**:
- Model: `text-embedding-3-large`
- Dimensions: 512 (optimal for speed/quality tradeoff)
- Batch Size: 100 texts per request
- Rate Limiting: Respects OpenAI rate limits
- Cost Tracking: Logs token count and estimated cost
- Caching: Results cached in Redis for 24h

**Scenarios**:
1. Embed 1000 document chunks
2. Estimated cost: ~$0.05 for 100k tokens
3. Retry on rate limit (429 response)
4. Cache frequently requested embeddings

**File**: `src/services/embeddings/openai_service.py`

---

## Metadata Enrichment Capability

### ADDED Requirement: LLM-Based Metadata Extraction

Use ChatOpenAI to extract rich metadata from document chunks.

**Specification**:
- Fields Extracted:
  - `summary` - Brief description (1-2 sentences)
  - `keywords` - List of key terms
  - `topic` - Primary topic classification
  - `complexity` - Level (simple/medium/complex)
  - `entities` - Named entities (people, places, orgs)
  - `sentiment` - Overall sentiment tone
- Model: ChatOpenAI (gpt-4o)
- Batch: Process documents in parallel
- Cost: ~$0.02 per 1000 tokens

**Scenarios**:
1. Extract metadata for 100 documents
2. Use metadata for filtering results
3. Topic clustering for related documents
4. Complexity-based ranking

**File**: `src/services/vector_store/metadata_handler.py`

---

## Retrieval Strategies Capability

### ADDED Requirement: RetrieverFactory with Multiple Strategies

Pluggable retrieval strategies for different query types.

**Specification**:
- Strategies:
  1. **Similarity** - Pure vector similarity search (k=5, fast)
  2. **MMR** - Maximum Marginal Relevance (k=5, diverse results)
  3. **Similarity + Filter** - Vector search with metadata filtering
  4. **Adaptive** - Query-type aware selection

- Methods:
  - `create_similarity_retriever(collection, k)` - Simple similarity
  - `create_mmr_retriever(collection, k, fetch_k, lambda)` - Diverse results
  - `create_filtered_retriever(collection, k, metadata_filter)` - With filters
  - `create_adaptive_retriever(collection, k, use_mmr, use_filters)` - Configurable
  - `get_recommended_retriever(collection, query_type)` - Auto-select

**Query Types**:
- `general` - Simple facts (similarity, k=5)
- `research` - Detailed analysis (MMR, k=5, diverse)
- `specific` - Domain-specific (filtered, k=3)
- `complex` - Multi-step reasoning (MMR + filters, k=5)

**Scenarios**:
1. General query → Use fast similarity
2. Research query → Use MMR for diversity
3. Specific query → Filter by topic first
4. Complex query → Use MMR + metadata filters

**File**: `src/services/retrievers/factory.py`

#### Requirement: Query Type Aware Retrieval

Automatic selection of best retrieval strategy based on query type.

**Specification**:
- Mapping:
  - `general` → Similarity (k=5, fast)
  - `research` → MMR (k=5, fetch_k=20, diverse)
  - `specific` → Filtered (k=3, topic match)
  - `complex` → MMR + Filtered (best quality)
- Decision: Based on query_type parameter
- Fallback: Default to general if unknown type

---

## Health & Monitoring Capability

### ADDED Requirement: Vector Store Health Checks

Monitor health of Qdrant connection and collections.

**Specification**:
- Endpoint: `GET https://qdrant-url/health`
- Checks:
  - Connection status
  - Collections count
  - Vector count per collection
  - Storage usage
- Frequency: On-demand (health checks)
- Circuit Breaker: Tracks failures and state

**Scenarios**:
1. Startup: Verify Qdrant is accessible
2. During operation: Monitor collection stats
3. Failure: Activate circuit breaker
4. Recovery: Attempt half-open state after timeout

---

## Architecture & Patterns

### Service Layer Pattern
- **Class**: QdrantVectorStoreManager
- **Location**: `src/services/vector_store/qdrant_manager.py`
- **Usage**: Encapsulates all Qdrant operations

### Factory Pattern
- **Class**: RetrieverFactory
- **Location**: `src/services/retrievers/factory.py`
- **Usage**: Create different retriever strategies

### Resilience Pattern
- **Circuit Breaker**: On repeated failures
- **Retry**: 3 attempts with backoff
- **Timeout**: 60s before recovery attempt

---

## Integration Points

**Phase 2** (Chunking):
- Consumes: Chunked documents with metadata
- Provides: Indexing pipeline

**Phase 4** (RAG Pipeline):
- Consumes: Retriever instances
- Provides: Retrieved context documents

**Phase 5** (Deployment):
- Container: Qdrant service in docker-compose
- Persistence: Volume-mounted storage

---

## Dependencies

```
langchain >= 0.1.0
langchain-openai >= 0.1.0
langchain-qdrant >= 1.1.0
qdrant-client >= 2.0.0
openai >= 1.0.0
redis >= 5.0.0
```

---

## Testing

- [x] test_pipeline_basic - Document indexing flow
- [x] test_similarity_retrieval - Similarity search
- [x] test_retriever_strategies - All 4 strategies
- [x] test_health_status - Health checks
- Result: **4/4 tests passing** ✓

---

## Status

- [x] Design approved
- [x] Implementation complete
- [x] Tests passing (4/4)
- [x] Integrated with Phase 2, 4, 5
- [x] Documentation complete
- [x] Production ready

**Completed**: December 22, 2025
