# Phase 1: Foundation & Infrastructure - Specification

**Change ID**: `phase-1-foundation`
**Version**: 1.0
**Status**: IMPLEMENTED

## Configuration Management Capability

### ADDED Requirements

#### Requirement: Centralized Environment Configuration

Configuration system using Pydantic V2 BaseSettings that loads from `.env` files and environment variables.

**Specification**:
- Model: `ProductionSettings` with `SettingsConfigDict`
- Supported variables:
  - `OPENAI_API_KEY` - OpenAI API key (required)
  - `OPENAI_MODEL` - Model name (default: gpt-4o)
  - `QDRANT_CLUSTER_ENDPOINT` - Qdrant URL
  - `QDRANT_API_KEY` - Qdrant authentication
  - `REDIS_URL` - Redis connection
  - `LANGSMITH_API_KEY` - LangSmith integration (optional)
  - `ENVIRONMENT` - Environment name (production/development)
  - `DEBUG` - Debug mode flag
  - `LOG_LEVEL` - Logging level

**Scenarios**:
1. Load from .env file on startup
2. Override with environment variables
3. Validate required fields (OPENAI_API_KEY)
4. Property aliases for backward compatibility

**File**: `src/config/settings.py`

---

## Logging & Observability Capability

### ADDED Requirements

#### Requirement: JSON-Structured Logging

Implement structured JSON logging using python-json-logger with context.

**Specification**:
- Format: JSON with timestamp, level, logger name, message
- Context: Include extra fields for tracing
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Output: stdout + file (logs/app.log)

**Scenarios**:
1. Log API requests with request ID
2. Track LLM API calls with token counts
3. Record errors with full stack traces
4. Performance metrics in logs

**File**: `src/utils/logging_config.py`

#### Requirement: Get Logger Function

Central function to get configured logger instances.

**Specification**:
- Function: `get_logger(name: str) -> logging.Logger`
- Returns pre-configured logger with JSON formatter
- Used throughout codebase for consistency

---

## Resilience & Error Handling Capability

### ADDED Requirements

#### Requirement: Circuit Breaker Pattern

Implement circuit breaker to prevent cascading failures.

**Specification**:
- States: CLOSED (normal) → OPEN (failure threshold exceeded) → HALF_OPEN (testing recovery)
- Threshold: 5 consecutive failures
- Timeout: 60 seconds before attempting recovery
- Metrics: Tracks failure count, success count, state transitions

**Scenarios**:
1. Qdrant Cloud connection fails → Circuit opens after 5 attempts
2. Circuit waits 60s, then tries recovery
3. Successful call → Circuit closes to CLOSED state
4. Continuous failures → Circuit stays OPEN

**File**: `src/utils/resilience.py`

#### Requirement: Retry Decorator

Decorator for automatic retry with exponential backoff.

**Specification**:
- Parameters:
  - `max_retries` - Maximum retry attempts (default: 3)
  - `backoff_factor` - Exponential backoff multiplier (default: 2)
  - `exceptions` - Tuple of exceptions to catch
- Delays: 1s, 2s, 4s (exponential)
- Logging: Each retry attempt logged

**Scenarios**:
1. API call fails → Retry after 1s
2. Second attempt fails → Retry after 2s
3. Third attempt succeeds → Return result
4. All retries exhausted → Raise exception

**File**: `src/utils/decorators.py`

#### Requirement: Caching Decorator

Decorator for caching function results.

**Specification**:
- TTL (Time To Live) configurable
- Key: Function name + arguments
- Backend: Redis for distributed cache
- Invalidation: Manual or TTL-based

**Scenarios**:
1. Cache expensive computations
2. Reduce API calls to external services
3. Automatic expiration after TTL

---

## Dependency Management Capability

### ADDED Requirements

#### Requirement: UV Package Manager Configuration

All project dependencies managed through UV (not pip or poetry).

**Specification**:
- Tool: UV for fast, deterministic dependency resolution
- Command Format:
  - Local development: `uv run python script.py` or `uv run pytest`
  - Dependency installation: `uv pip install package`
  - Lock file: `uv.lock` for reproducibility
- Configuration File: `pyproject.toml` or `requirements.txt`
- Docker Integration: UV used in multi-stage builds for faster image creation
- CI/CD: All automation scripts use `uv run` prefix

**Scenarios**:
1. Development: `uv run python -m pytest` (with UV venv)
2. Testing: `uv run test_phase4_integration.py`
3. Docker Build: `RUN uv pip install -r requirements.txt` in Dockerfile
4. Dependency lock: `uv.lock` ensures consistent installs across environments

**Important Notes**:
- UV MUST be installed before running any project commands
- All scripts should use `uv run` not raw `python`
- Docker Dockerfile updated to use UV for dependency installation
- Local development setup: `pip install uv` then `uv run`

**File**: Configuration in `pyproject.toml` / `requirements.txt`

---

## Token & Cost Tracking Capability

### ADDED Requirements

#### Requirement: Token Counting

Integration with tiktoken for accurate token counting.

**Specification**:
- Model: gpt-4o (cl100k_base encoding)
- Usage:
  - Count tokens before sending to API
  - Track cumulative tokens for cost calculation
  - Support for different models
- Functions:
  - `count_tokens(text: str, model: str) -> int`
  - `estimate_cost(tokens: int) -> float`

**Scenarios**:
1. Chunk documents → Count tokens to verify size
2. Send prompt to LLM → Log token count
3. Track monthly usage → Calculate costs
4. Alert on quota approaching

**File**: `src/utils/decorators.py` + `src/config/settings.py`

---

## Architecture & Patterns

### Configuration Pattern
- **Type**: Pydantic V2 BaseSettings
- **Location**: `src/config/settings.py`
- **Access**: `from src.config.settings import settings`
- **Singleton**: Global `settings` instance used throughout

### Logging Pattern
- **Type**: Factory pattern with JSON formatter
- **Location**: `src/utils/logging_config.py`
- **Access**: `logger = get_logger(__name__)`
- **Format**: JSON with context fields

### Resilience Pattern
- **Type**: Circuit Breaker + Decorator pattern
- **Location**: `src/utils/resilience.py`, `src/utils/decorators.py`
- **Usage**: `@retry_with_backoff()` or `CircuitBreaker()`

---

## Dependencies Added

```
pydantic >= 2.0
pydantic-settings >= 2.0
python-json-logger >= 2.0
tiktoken >= 0.5
python-dotenv >= 1.0
```

---

## Related Phases

- **Phase 2** (Chunking): Uses configuration for chunk sizes, logging for pipeline tracking
- **Phase 3** (Vector Store): Uses circuit breaker for Qdrant calls, retry decorator for API failures
- **Phase 4** (RAG Pipeline): Uses logging for metrics, token counting for cost tracking
- **Phase 5** (Deployment): Uses configuration for environment setup

---

## Status

- [x] Design approved
- [x] Implementation complete
- [x] Tests written and passing
- [x] Documentation complete
- [x] Code review approved
- [x] Merged to main

**Completed**: December 22, 2025