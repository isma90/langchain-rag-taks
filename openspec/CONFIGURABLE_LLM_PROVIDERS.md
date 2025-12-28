# Configurable LLM Providers

## Overview

Flexible LLM provider configuration allowing selection between OpenAI and Google Gemini for different pipeline stages without code changes.

## Problem Solved

- **Vendor Lock-in**: System was hardcoded to use Gemini
- **Cost Optimization**: Different tasks have different cost/quality tradeoffs
- **Flexibility**: Need to switch providers for experimentation or cost control

## Solution Architecture

### Configuration Variables

Three independent provider selections:

```bash
# Embeddings (Step 5)
EMBEDDINGS_PROVIDER=openai|gemini

# Metadata Extraction (Step 4)
METADATA_PROVIDER=openai|gemini

# Q&A Generation (Step 7)
QA_PROVIDER=openai|gemini
```

### Factory Pattern Implementation

**embeddings_factory.py**
```python
def create_embeddings_service(provider: Optional[str] = None):
    """Create embeddings service based on provider configuration."""
    provider = provider or settings.embeddings_provider

    if provider == 'gemini':
        return GeminiEmbeddingsService()
    elif provider == 'openai':
        return EmbeddingsService(use_large=True)
```

**metadata_handler.py**
```python
def __init__(self, provider: Optional[str] = None):
    """Initialize with configurable LLM provider."""
    provider = provider or settings.metadata_provider

    if provider == 'gemini':
        self.llm = ChatGoogleGenerativeAI(...)
    elif provider == 'openai':
        self.llm = ChatOpenAI(...)
```

### Supported Providers

**OpenAI**
- Models: gpt-4o, gpt-4o-mini
- Embeddings: text-embedding-3-large (3072 dims → 512 dims reduced)
- Cost: Higher, better quality
- Speed: Standard

**Google Gemini**
- Models: gemini-2.5-flash, gemini-2.0-flash
- Embeddings: embedding-001 (768 dims)
- Cost: Lower, competitive quality
- Speed: Fast

## Configuration Examples

### Default (Recommended)
```bash
EMBEDDINGS_PROVIDER=openai
METADATA_PROVIDER=openai
QA_PROVIDER=openai
```

### Cost-Optimized
```bash
EMBEDDINGS_PROVIDER=gemini
METADATA_PROVIDER=gemini
QA_PROVIDER=gemini
```

### Hybrid (Cost + Quality)
```bash
EMBEDDINGS_PROVIDER=gemini      # Cheap
METADATA_PROVIDER=gemini        # Cheap
QA_PROVIDER=openai              # Better quality
```

### Full OpenAI
```bash
EMBEDDINGS_PROVIDER=openai
METADATA_PROVIDER=openai
QA_PROVIDER=openai
```

## Cost Comparison

| Configuration | Per Doc | Per 100 Docs/Month |
|---|---|---|
| All Gemini | $0.01 | $1 |
| Hybrid (Gemini + OpenAI Q&A) | $0.03 | $3 |
| All OpenAI | $0.15 | $15 |

## API Keys Required

### For Gemini
```bash
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
```

### For OpenAI
```bash
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

## How to Change Providers

1. Update `.env` or docker-compose.yml:
```bash
EMBEDDINGS_PROVIDER=openai
METADATA_PROVIDER=openai
QA_PROVIDER=openai
```

2. Rebuild and restart:
```bash
podman-compose down
podman-compose build
podman-compose up -d
```

3. Verify in logs:
```bash
podman logs rag-api | grep -i "provider"
```

## Implementation Details

### Settings Validation

```python
@field_validator('embeddings_provider')
def validate_embeddings_provider(cls, v: str) -> str:
    if v.lower() not in ['gemini', 'openai']:
        raise ValueError(...)
    return v.lower()
```

### Dynamic Service Creation

```python
# Services instantiate based on settings
embeddings = create_embeddings_service()  # Uses EMBEDDINGS_PROVIDER
handler = MetadataHandler()               # Uses METADATA_PROVIDER
```

### No Code Changes Required

All provider switching done via environment variables. No deployment of code necessary.

## Files Modified

- `src/config/settings.py` - Added provider configuration fields
- `src/services/embeddings/embeddings_factory.py` - Factory pattern
- `src/services/vector_store/metadata_handler.py` - Configurable LLM
- `src/services/vector_store/qdrant_manager.py` - Uses factory
- `docker-compose.yml` - Environment variables

## Status

✅ **Implemented**: All three provider selections configurable
✅ **Tested**: Switching between providers works correctly
✅ **Documented**: Clear examples and cost comparisons

## Future Enhancements

- Add Anthropic Claude support
- Add Azure OpenAI support
- Provider performance benchmarks
- Automatic cost optimization recommendations
