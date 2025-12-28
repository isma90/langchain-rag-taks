# Qdrant Cloud Vector Database Integration

## Overview

Migration from self-hosted Qdrant Docker container to fully managed Qdrant Cloud service for improved reliability, scalability, and maintenance.

## Problem Solved

- **Local Qdrant Issues**: 404 errors on collection health checks
- **Operational Overhead**: Managing Docker container lifecycle
- **Scalability**: Local instance limited by machine resources
- **Availability**: No built-in redundancy or backups

## Solution Architecture

### Service Architecture

**Before**: Self-hosted Qdrant container
```yaml
docker-compose.yml:
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports: [6333, 6334]
    volumes: [qdrant-data, qdrant-snapshots]
```

**After**: Qdrant Cloud (managed service)
```bash
QDRANT_CLUSTER_ENDPOINT=https://xxx.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Configuration

**Environment Variables**
```bash
# Qdrant Cloud endpoint (HTTPS)
QDRANT_CLUSTER_ENDPOINT=https://your-cluster-id.region.cloud.qdrant.io

# API key for authentication
QDRANT_API_KEY=your_jwt_token

# Collection name (same as before)
QDRANT_COLLECTION_NAME=rag_documents
```

**Docker Compose Changes**
```yaml
# Removed qdrant service entirely
# Removed qdrant volumes
# Updated API environment to use cloud endpoint
environment:
  QDRANT_CLUSTER_ENDPOINT: ${QDRANT_CLUSTER_ENDPOINT}
  QDRANT_API_KEY: ${QDRANT_API_KEY}

# No longer depends on local qdrant service
depends_on:
  redis:
    condition: service_healthy
```

### Connection Configuration

**Automatic**: QdrantClient auto-detects HTTPS and authenticates:

```python
class QdrantVectorStoreManager:
    def __init__(self, url, api_key):
        self.client = QdrantClient(
            url=url,              # https://xxx.cloud.qdrant.io
            api_key=api_key,      # JWT token
            timeout=30,
        )
        # Automatically uses HTTPS and API key for auth
```

## Migration Steps

1. **Set Environment Variables** (done in .env)
```bash
QDRANT_CLUSTER_ENDPOINT=https://...cloud.qdrant.io
QDRANT_API_KEY=eyJ...
```

2. **Remove Local Qdrant from Docker Compose**
```bash
git diff docker-compose.yml
# Shows removed qdrant service and volumes
```

3. **Rebuild and Deploy**
```bash
podman-compose down
podman-compose build
podman-compose up -d
```

4. **Verify Connection**
```bash
curl -X GET "https://xxx.cloud.qdrant.io/health" \
  -H "api-key: $QDRANT_API_KEY"
```

## Benefits

✅ **Reliability**: 99.9% SLA with automated failover
✅ **Scalability**: Auto-scales vector database capacity
✅ **Maintenance**: No infrastructure management
✅ **Security**: Enterprise authentication and encryption
✅ **Backups**: Automatic daily backups
✅ **Monitoring**: Built-in metrics and dashboards
✅ **Performance**: Global CDN for low latency

## Pricing

**Qdrant Cloud Pricing Model**
- Compute: $0.095 per compute unit per hour
- Storage: $0.10 per GB per month
- Network: $0.05 per GB egress

**Typical Usage**
- Small collection (1M vectors): ~$50-100/month
- Medium collection (10M vectors): ~$200-400/month
- Large collection (100M+ vectors): ~$1000+/month

## Error Handling

### Collection Health Checks

**Issue**: Local Qdrant returned 404 on collection existence checks

**Solution**: Improved error handling in QdrantManager:

```python
try:
    vector_store = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        url=url,
        api_key=api_key,
        force_recreate=force_recreate,
    )
except Exception as e:
    # Retry with force_recreate=True
    vector_store = QdrantVectorStore.from_documents(
        ...,
        force_recreate=True,  # Force recreation
    )
```

### Connection Verification

Monitor connection health:
```bash
# Check collection exists
curl -X GET "https://xxx.cloud.qdrant.io/collections" \
  -H "api-key: $QDRANT_API_KEY"

# Check stats
curl -X GET "https://xxx.cloud.qdrant.io/collections/rag_documents" \
  -H "api-key: $QDRANT_API_KEY"
```

## Network Architecture

```
┌─────────────┐
│  Frontend   │
│  (3000)     │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│   FastAPI Backend       │
│   (8000)                │
├─────┬────────┬──────────┤
│     │        │          │
│  Redis  Qdrant Cloud   OpenAI
│  (6379) (HTTPS)        API
│         + API Key
└────────────────────────┘
```

## Files Modified

- `docker-compose.yml` - Removed qdrant service and volumes
- `.env` - Added QDRANT_CLUSTER_ENDPOINT and API key
- `src/services/vector_store/qdrant_manager.py` - Improved error handling

## Status

✅ **Migrated**: Using Qdrant Cloud exclusively
✅ **Tested**: Connections working properly
✅ **Monitoring**: Health checks active

## Future Enhancements

- Multi-region redundancy
- Sharding for very large collections
- Advanced authentication (OAuth, SAML)
- VPC endpoint for private connectivity
- Custom SLA options
