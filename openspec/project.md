# Project Context - RAG System (Retrieval-Augmented Generation)

## 🎯 Purpose

Build a **production-ready Retrieval-Augmented Generation (RAG) system** that combines:
- Advanced document processing and chunking strategies
- Vector database (Qdrant Cloud) for semantic search
- Large Language Models (OpenAI GPT-4o) for intelligent answers
- REST API for question-answering with multiple retrieval strategies
- Containerized deployment with Docker/Docker Compose

**Core objectives from Tarea_RAG_1:**
1. ✅ Create account in Qdrant Cloud and configure external vector database
2. ✅ Implement smart chunking strategies (Recursive, Semantic, Markdown, HTML)
3. ✅ Build metadata enrichment for indexed documents
4. ✅ Deploy RAG pipeline with LLM integration
5. ✅ Create evaluation datasets (answerable and non-answerable questions)
6. ✅ Containerize for production deployment
7. 🔄 Build frontend UI for interactive question-answering

## 🛠 Tech Stack

### Backend
- **Python 3.11** - Core language
- **UV** - Python package manager and dependency resolver (REQUIRED)
- **FastAPI + Uvicorn** - REST API framework
- **LangChain** - LLM orchestration (chains, retrievers, memory)
- **OpenAI API** - GPT-4o for answer generation, text-embedding-3-large for embeddings
- **Qdrant** - Vector database (Cloud hosted or Docker local)
- **Redis** - Caching layer
- **Pydantic** - Data validation and settings management
- **Tiktoken** - Token counting for precise chunking

### DevOps
- **Docker & Docker Compose** - Containerization and orchestration
- **Bash Scripts** - Deployment automation (local and remote SSH)
- **UV** - Dependency management in Docker builds
- **Nginx** - Reverse proxy (future)

### Frontend (Phase 6 - Proposed)
- **React 19.2.3 + TypeScript** - UI framework
- **Vite 5.0+** - Build tool
- **Tailwind CSS 3.4+** - Styling (utility-first)
- **Axios 1.6+** - HTTP client
- **React Router 7.0+** - Client-side routing
- **Vitest + React Testing Library** - Testing framework
- **Playwright/Cypress** - E2E testing

### Infrastructure
- **Qdrant Cloud** - Managed vector database
- **OpenAI API** - LLM and embeddings service
- **Docker containers** - API, Qdrant, Redis services

## 📋 Project Conventions

### Code Style
- **Python**: PEP 8 compliant, black-formatted (implicit)
- **Naming**:
  - Classes: PascalCase (e.g., `RAGService`)
  - Functions: snake_case (e.g., `answer_question`)
  - Constants: UPPER_SNAKE_CASE (e.g., `CHUNK_SIZE`)
  - Private members: leading underscore (e.g., `_rag_service`)
- **Type Hints**: Always use for function parameters and returns
- **Docstrings**: Google-style for all public functions/classes
- **Logging**: JSON structured logs with context

### Architecture Patterns
- **Factory Pattern**: `ChunkingFactory`, `RetrieverFactory` for creating objects
- **Service Layer**: `RAGService`, `QdrantVectorStoreManager` encapsulate business logic
- **Pipeline Pattern**: `RAGPipelineIntegrator` orchestrates complex workflows
- **Chain of Responsibility**: LangChain LCEL chains for composable operations
- **Strategy Pattern**: Multiple chunking and retrieval strategies
- **Singleton**: Global state management for RAG service instance

### Directory Structure
```
langchain-rag-taks/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py            # FastAPI app, endpoints
│   │   └── __init__.py
│   ├── config/                 # Configuration
│   │   ├── settings.py         # Pydantic settings
│   │   └── __init__.py
│   ├── services/               # Business logic
│   │   ├── chunking/           # Document chunking
│   │   │   ├── factory.py
│   │   │   └── __init__.py
│   │   ├── embeddings/         # Embedding generation
│   │   │   ├── openai_service.py
│   │   │   └── __init__.py
│   │   ├── vector_store/       # Vector DB integration
│   │   │   ├── qdrant_manager.py
│   │   │   ├── metadata_handler.py
│   │   │   └── __init__.py
│   │   ├── retrievers/         # Retrieval strategies
│   │   │   ├── factory.py
│   │   │   └── __init__.py
│   │   └── rag/                # RAG orchestration
│   │       ├── pipeline_integrator.py
│   │       ├── chain_builder.py
│   │       ├── rag_service.py
│   │       └── __init__.py
│   └── utils/                  # Utilities
│       ├── logging_config.py
│       ├── resilience.py       # Circuit breaker
│       ├── decorators.py       # Retry logic
│       └── __init__.py
├── tests/                      # Test files
│   ├── test_phase*.py
│   └── conftest.py
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Multi-container orchestration
├── deploy.sh                   # Local deployment script
├── remote-deploy.sh            # Remote SSH deployment
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .dockerignore               # Docker build optimization
├── DEPLOYMENT.md               # Deployment documentation
├── INFRASTRUCTURE.md           # Infrastructure documentation
└── openspec/
    ├── project.md             # This file
    └── AGENTS.md              # AI assistant guidelines
```

### Testing Strategy
- **Integration Tests**: `test_phase*.py` files validate end-to-end pipelines
- **Test Framework**: pytest with async support
- **Coverage Areas**:
  - Phase 3: Vector store and indexing operations
  - Phase 4: RAG chain and question-answering
  - Phase 5: Docker containerization and deployment
- **CI/CD**: Manual testing via scripts (GitHub Actions planned)

### Git Workflow
- **Branches**:
  - `main` - Production-ready code
  - Feature branches for development
- **Commits**: Descriptive messages with context
- **Format**: `[Phase X] Description of changes`

## 📚 Domain Context

### RAG System Architecture
**RAG (Retrieval-Augmented Generation)** combines:
1. **Retrieval**: Find relevant documents using vector similarity search
2. **Augmentation**: Use retrieved documents as context
3. **Generation**: LLM generates answers based on context

### Key Concepts

#### Chunking Strategies
- **Recursive**: Split by hierarchical separators (best general-purpose)
- **Semantic**: AI-based intelligent chunking (advanced)
- **Markdown**: Preserve structure for technical docs
- **HTML**: Handle web content structure
- **Token-based**: Measure size in LLM tokens (not characters)

#### Retrieval Strategies
- **Similarity**: Pure vector similarity (cosine distance)
- **MMR (Maximum Marginal Relevance)**: Balance relevance with diversity
- **Filtered**: Metadata-based filtering + similarity
- **Adaptive**: Query-type aware selection

#### Query Types
- **General**: Simple facts, straightforward answers
- **Research**: Comparative analysis, multiple sources
- **Specific**: Domain-specific technical questions
- **Complex**: Multi-step reasoning, synthesis

#### Metadata Enrichment
Each chunk includes extracted:
- **summary**: Brief description of content
- **keywords**: Extracted key terms
- **topic**: Primary topic classification
- **complexity**: Content complexity level
- **entities**: Named entities (people, places, orgs)
- **sentiment**: Overall sentiment (for social content)

### Vector Database (Qdrant)
- **Collection**: Named vector index (e.g., "rag_documents")
- **Points**: Individual documents with metadata and embeddings
- **Embeddings**: OpenAI text-embedding-3-large (512 dimensions)
- **Operations**: Create, search, update, delete collections/points

## ⚙️ Important Constraints

### Technical
- **Python Version**: Must be 3.11+ (for type hints and performance)
- **Package Manager**: UV REQUIRED for dependency management (not pip or poetry)
  - All project commands use `uv run` or `uv pip`
  - Local development must install UV: `pip install uv` or system package
  - Docker builds use UV for fast, deterministic dependency installation
- **Token Limits**:
  - Chunk size measured in tokens (1000 default)
  - OpenAI API rate limits (RPM and TPM)
- **API Keys**: Must be stored in .env, never committed to git
- **Qdrant Cloud**: External dependency, requires valid credentials
- **Docker**: Requires Docker >= 20.10, Docker Compose >= 1.29

### Performance
- **Chunk Processing**: Must handle large documents efficiently
- **API Response Time**: Target < 5 seconds for question-answering
- **Memory Usage**: Container limited to available RAM
- **Concurrent Requests**: Rate limiting enforced (10 RPM default)

### Deployment
- **Staging**: docker-compose for local/dev
- **Production**: Docker with separate orchestration (Kubernetes future)
- **Data Persistence**: Volume-mounted storage for Qdrant and Redis
- **Secrets**: Environment variables for sensitive data

## 🔗 External Dependencies

### APIs
- **OpenAI API**:
  - `gpt-4o` for answer generation
  - `text-embedding-3-large` for embeddings
  - Rate limits: ~10-50 requests/minute (depending on tier)
  - Cost: ~$0.05 per 1K input tokens

- **Qdrant Cloud**:
  - Vector database hosting
  - API endpoint: `https://<id>.us-east4-0.gcp.cloud.qdrant.io`
  - Free tier: 25GB vectors
  - Authentication: API key required

### Services
- **Redis**: Caching service (Docker container or external)
- **Docker Hub**: Image registry for base images

### Libraries
- **langchain**: ^0.1.0 - LLM framework
- **langchain-openai**: ^0.1.0 - OpenAI integration
- **langchain-qdrant**: ^1.1.0 - Qdrant vector store
- **fastapi**: ^0.104.0 - Web framework
- **pydantic**: ^2.0 - Data validation
- **pydantic-settings**: ^2.0 - Configuration management
- **tiktoken**: ^0.5.0 - Token counting
- **redis**: ^5.0 - Redis client
- **httpx**: ^0.25.0 - Async HTTP
- **tenacity**: ^8.2.0 - Retry logic

## 📊 Current Implementation Status

### ✅ Completed (Phases 1-5)
- **Phase 1**: Logging, configuration, utilities, resilience patterns
- **Phase 2**: 4 chunking strategies (recursive, semantic, markdown, HTML) with token-based sizing
- **Phase 3**: Vector store integration (Qdrant Cloud) with metadata enrichment and 4 retrieval strategies
- **Phase 4**: RAG pipeline with LCEL chains, 4 query-type specific prompts, RAGService
- **Phase 5**: Docker containerization, FastAPI REST API, deployment scripts

### 🔄 Proposed (Phase 6)
- **Phase 6**: Frontend UI - Interactive chatbot (React 19 + TypeScript + Vite)
  - Chat interface with message history and streaming responses
  - Document management (upload, list, delete)
  - Query configuration (type selector, retrieval parameters)
  - Responsive design (mobile-first, 3 breakpoints)
  - WCAG 2.1 Level AA accessibility
  - Dark/light theme support
  - Session persistence (localStorage, Phase 7: backend)
  - Status: PROPOSED (awaiting approval for implementation)

### 📋 Planned
- **Phase 7**: Backend Session Storage + Evaluation Datasets
  - Save conversations to backend (IndexedDB/API)
  - Create evaluation datasets (QA pairs)
  - Multi-user support setup
- **Phase 8**: Production Monitoring & Analytics
  - Prometheus/Grafana for metrics
  - User analytics
  - Error tracking (Sentry)
- **Phase 9**: Advanced Features
  - Real-time collaboration (WebSockets)
  - AI-powered suggestions
  - Document annotation

## 🎯 Success Criteria

From original task requirements:
1. ✅ RAG system deployable via URL with accessible playground
2. ✅ Document loading script with documented strategy
3. 🔄 Evaluation datasets (answerable + non-answerable questions)
4. 🔄 Interactive frontend for question-answering
5. ✅ Production-ready containerized deployment

## 📝 Important Notes

- All `.env` files must be git-ignored (contains API keys)
- Docker volumes persist data between container restarts
- Remote deployment via SSH requires public key authentication or password
- API rate limiting prevents abuse (default: 10 requests/minute)
- Qdrant Cloud has free tier limits (25GB vectors)
- Local development can use Docker Qdrant instead of Cloud
