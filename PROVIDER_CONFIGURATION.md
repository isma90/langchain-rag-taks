# Provider Configuration Guide

## Overview

The RAG system now supports configurable LLM providers for different tasks. You can switch between **OpenAI** and **Google Gemini** without changing any code - just update environment variables and restart the services.

## Available Providers

### Supported Services

1. **Embeddings** (Step 5): Convert text to vectors
   - Options: `gemini`, `openai`
   - Default: `gemini` (768 dims, $0.00001/1k tokens)

2. **Metadata Extraction** (Step 4): Extract summary, keywords, topics
   - Options: `gemini`, `openai`
   - Default: `gemini` (gemini-2.5-flash)

3. **Q&A Generation** (Step 7): Answer user questions
   - Options: `gemini`, `openai`
   - Default: `openai` (gpt-4o-mini)

## Configuration

### Environment Variables

Add these to your `.env` file or docker-compose.yml:

```bash
# Choose embeddings provider: gemini or openai
EMBEDDINGS_PROVIDER=gemini

# Choose metadata extraction provider: gemini or openai
METADATA_PROVIDER=gemini

# Choose Q&A provider: gemini or openai
QA_PROVIDER=openai
```

### Examples

#### 1. Default Configuration (Recommended for cost)
```bash
EMBEDDINGS_PROVIDER=gemini      # Gemini embeddings (768 dims)
METADATA_PROVIDER=gemini        # Gemini metadata extraction
QA_PROVIDER=openai              # OpenAI for Q&A (better quality)

Cost: ~$0.03/document
```

#### 2. All OpenAI
```bash
EMBEDDINGS_PROVIDER=openai      # text-embedding-3-large (3072 dims)
METADATA_PROVIDER=openai        # gpt-4o-mini
QA_PROVIDER=openai              # gpt-4o-mini

Cost: ~$0.15/document
Quality: Best
```

#### 3. All Gemini
```bash
EMBEDDINGS_PROVIDER=gemini      # Gemini embeddings
METADATA_PROVIDER=gemini        # gemini-2.5-flash
QA_PROVIDER=gemini              # gemini-2.5-flash

Cost: ~$0.01/document
Speed: Fast (flash model)
```

#### 4. Hybrid (Gemini for cost, OpenAI for Q&A quality)
```bash
EMBEDDINGS_PROVIDER=gemini      # Cheap embeddings
METADATA_PROVIDER=gemini        # Cheap metadata extraction
QA_PROVIDER=openai              # Better Q&A quality

Cost: ~$0.03/document
Balance: Cost + Quality
```

## How to Change Providers

### Step 1: Update Environment Variables

Edit `.env`:
```bash
EMBEDDINGS_PROVIDER=openai
METADATA_PROVIDER=openai
QA_PROVIDER=openai
```

Or in `docker-compose.yml`:
```yaml
environment:
  EMBEDDINGS_PROVIDER: openai
  METADATA_PROVIDER: openai
  QA_PROVIDER: openai
```

### Step 2: Rebuild and Restart

```bash
# Using podman-compose
podman-compose down
podman-compose build rag-api
podman-compose up -d

# Or using docker-compose
docker-compose down
docker-compose build rag-api
docker-compose up -d
```

### Step 3: Verify Configuration

Check the logs to confirm which providers are loaded:

```bash
# Check if providers are correctly initialized
podman logs rag-api | grep -i "provider\|metadata\|embedding"
```

## Cost Comparison

### Per Document Processing

| Configuration | Embeddings | Metadata | Q&A | Total |
|---|---|---|---|---|
| Gemini Only | $0.001 | $0.002 | $0.007 | ~$0.01 |
| Default (Gemini+OpenAI) | $0.001 | $0.002 | $0.02 | ~$0.03 |
| OpenAI Only | $0.01 | $0.05 | $0.05 | ~$0.15 |

### Monthly (100 documents)

| Configuration | Monthly Cost |
|---|---|
| Gemini Only | $1 |
| Default (Gemini+OpenAI) | $3 |
| OpenAI Only | $15 |

## API Keys Required

Depending on which providers you use, you need:

### For Gemini
```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash  # or another Gemini model
```

### For OpenAI
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini  # or another OpenAI model
```

## Rate Limiting

All providers respect the configured rate limit:
```bash
RATE_LIMIT_RPM=10  # Requests per minute
```

This is a **global limit** across all providers.

## Performance Characteristics

### Gemini
- **Speed**: Fast (especially gemini-2.5-flash)
- **Cost**: Very low ($0.00001/1k tokens for embeddings)
- **Embeddings**: 768 dimensions
- **Quality**: Good for metadata extraction, acceptable for Q&A

### OpenAI
- **Speed**: Standard
- **Cost**: Higher ($0.00005/1k tokens for embeddings)
- **Embeddings**: Up to 3072 dimensions
- **Quality**: Excellent for all tasks

## Troubleshooting

### Error: "Unsupported embeddings provider"
- Check that EMBEDDINGS_PROVIDER is set to 'gemini' or 'openai'
- Ensure you restarted the containers after changing the variable

### API calls failing with provider X
- Verify the API key is set correctly (GEMINI_API_KEY or OPENAI_API_KEY)
- Check rate limiting isn't blocking requests
- Review logs: `podman logs rag-api`

### Embeddings dimension mismatch
- Different providers use different embedding dimensions:
  - Gemini: 768 dimensions
  - OpenAI: 512 dimensions (reduced from 3072)
- The system handles this automatically, but note that changing providers mid-collection may require re-indexing

## Implementation Details

### Embeddings Factory
The system uses a factory pattern (`embeddings_factory.py`) to instantiate the correct embeddings service:

```python
from src.services.embeddings.embeddings_factory import create_embeddings_service

# Uses EMBEDDINGS_PROVIDER env var
embeddings = create_embeddings_service()

# Or override
embeddings = create_embeddings_service(provider='openai')
```

### Metadata Handler
The metadata handler detects the configured provider on initialization:

```python
from src.services.vector_store.metadata_handler import MetadataHandler

# Uses METADATA_PROVIDER env var
handler = MetadataHandler()

# Or override
handler = MetadataHandler(provider='openai')
```

## Advanced Usage

### Dynamic Provider Switching
You can override the default provider at runtime (in code):

```python
from src.services.embeddings.embeddings_factory import create_embeddings_service
from src.services.vector_store.metadata_handler import MetadataHandler

# Use OpenAI for embeddings this time
embeddings = create_embeddings_service(provider='openai')

# Use Gemini for metadata this time
handler = MetadataHandler(provider='gemini')
```

### Checking Active Configuration
The settings object stores provider configuration:

```python
from src.config.settings import settings

print(f"Embeddings: {settings.embeddings_provider}")
print(f"Metadata: {settings.metadata_provider}")
print(f"Q&A: {settings.qa_provider}")
```
