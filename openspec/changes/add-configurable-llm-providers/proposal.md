# Change: Add Configurable LLM Providers

## Why

The system was hardcoded to use single LLM providers, preventing cost optimization and vendor flexibility. Different pipeline stages (embeddings, metadata, Q&A) have different cost/quality tradeoffs that benefit from independent provider selection.

## What Changes

- Support both OpenAI and Google Gemini as configurable providers
- Allow independent provider selection for embeddings, metadata extraction, and Q&A generation
- Implement factory pattern for dynamic service creation based on configuration
- Enable cost optimization by using cheaper providers for some tasks, premium for others

## Impact

- **Affected specs**: `llm-configuration`
- **Affected code**:
  - `src/config/settings.py` - New configuration fields
  - `src/services/embeddings/embeddings_factory.py` - Factory pattern for embeddings
  - `src/services/vector_store/metadata_handler.py` - Configurable LLM selection
  - `src/services/rag/chain_builder.py` - Uses configurable LLM
  - `docker-compose.yml` - Environment variables for providers
- **Breaking changes**: None - OpenAI remains default
- **User impact**: Cost savings (30-70% reduction), vendor flexibility, no code changes needed
