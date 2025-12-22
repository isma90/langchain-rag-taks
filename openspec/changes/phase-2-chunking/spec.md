# Phase 2: Text Chunking - Specification

**Change ID**: `phase-2-chunking`
**Version**: 1.0
**Status**: IMPLEMENTED

## Document Chunking Capability

### ADDED Requirements

#### Requirement: ChunkingFactory with Multiple Strategies

Pluggable document chunking factory supporting multiple splitting strategies.

**Specification**:
- Class: `ChunkingFactory`
- Methods:
  - `create_recursive(chunk_size, chunk_overlap)` → RecursiveCharacterTextSplitter
  - `create_semantic(chunk_size, chunk_overlap)` → SemanticChunker
  - `create_markdown(chunk_size, chunk_overlap)` → MarkdownHeaderTextSplitter
  - `create_html(chunk_size, chunk_overlap)` → HTMLHeaderTextSplitter
- Sizing: All use token-based measurements via tiktoken
- Default: chunk_size=1000 tokens, overlap=200 tokens

**Scenarios**:
1. Load PDF → Use recursive strategy
2. Load technical docs → Use markdown strategy
3. Load web content → Use HTML strategy
4. Load general text → Use semantic strategy

**File**: `src/services/chunking/factory.py`

#### Requirement: Recursive Character Splitting

Baseline chunking strategy using hierarchical separators.

**Specification**:
- Separators: `["\n\n", "\n", " ", ""]` (try in order)
- Benefits: Fast, general-purpose, preserves paragraph structure
- Token-counted sizing: Ensures chunks don't exceed token limit
- Overlap: Prevents losing context at chunk boundaries

**Scenarios**:
1. General text documents
2. Mixed format content
3. When structure is minimal

#### Requirement: Semantic Chunking

AI-based intelligent splitting that respects conceptual boundaries.

**Specification**:
- Uses LangChain's SemanticChunker
- Breaks chunks when semantic similarity drops
- More expensive (more LLM calls) but better quality
- Token-counted sizing applied post-splitting

**Scenarios**:
1. Complex technical documentation
2. When semantic coherence matters most
3. When document quality is critical

#### Requirement: Markdown-Aware Splitting

Structure-preserving splitting for Markdown documents.

**Specification**:
- Preserves heading hierarchy
- Maintains code blocks intact
- Headers become context for subsequent chunks
- Token-counted sizing per section

**Scenarios**:
1. README files
2. Technical documentation in Markdown
3. API documentation
4. Blog posts with structure

#### Requirement: HTML-Aware Splitting

Web content-aware splitting with tag consideration.

**Specification**:
- Understands HTML structure (div, section, article, etc.)
- Preserves semantic tags
- Cleans formatting while preserving structure
- Token-counted sizing

**Scenarios**:
1. Web scraping results
2. HTML documentation
3. Blog posts in HTML format

---

## Token-Based Sizing

### ADDED Requirement: Token-Counted Chunking

All chunking strategies measure size in tokens, not characters.

**Specification**:
- Model: gpt-4o (using cl100k_base encoding via tiktoken)
- Measurement: Tokens counted before adding to chunk
- Sizing: chunk_size in tokens (default 1000)
- Validation: Chunks never exceed configured token limit

**Scenarios**:
1. Chunk size of "1000 tokens" = ~4000 characters (ratio varies by content)
2. Ensures LLM can process all chunks within context window
3. Accurate cost estimation based on actual token usage

---

## Metadata Preservation

### ADDED Requirement: Maintain Metadata Through Chunking

Document metadata propagates through chunking process.

**Specification**:
- Original metadata preserved in each chunk
- Fields: source, page, author, created_date, etc.
- Enables filtering/sorting at retrieval time
- Used by Phase 3 for enrichment

---

## Architecture & Patterns

### Factory Pattern
- **Pattern**: Factory for strategy selection
- **Benefit**: Easy to add new strategies
- **Location**: `src/services/chunking/factory.py`

### Strategy Pattern
- **Pattern**: Each strategy is independent implementation
- **Benefit**: Swap strategies without changing consumer code
- **Interface**: All return LangChain Document objects

---

## Integration Points

**Phase 3** (Vector Store):
- Consumes chunked documents
- Uses chunk boundaries for indexing
- Metadata used for filtering

**Phase 4** (RAG Pipeline):
- Chunks become context for LLM
- Quality of chunks affects answer quality

---

## Dependencies

```
langchain >= 0.1.0
langchain-text-splitters >= 0.0.1
tiktoken >= 0.5
```

---

## Status

- [x] Design approved
- [x] Implementation complete (4 strategies)
- [x] Tests written and passing
- [x] Integrated with Phase 3 & 4
- [x] Documentation complete

**Completed**: December 22, 2025