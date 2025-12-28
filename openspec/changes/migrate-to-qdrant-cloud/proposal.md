# Change: Migrate to Qdrant Cloud

## Why

Local Docker-based Qdrant had operational issues (404 errors on health checks), no built-in backups, manual container management overhead, and scalability limitations. Migration to Qdrant Cloud provides enterprise reliability, automatic failover, and reduced operational burden.

## What Changes

- Remove local Qdrant Docker service from docker-compose.yml
- Configure system to use Qdrant Cloud managed service
- Use HTTPS endpoint with JWT API key authentication
- Implement retry logic for collection creation failures
- Simplify deployment by removing local vector database management

## Impact

- **Affected specs**: `vector-storage`
- **Affected code**:
  - `docker-compose.yml` - Remove qdrant service, add environment variables
  - `src/services/vector_store/qdrant_manager.py` - Add retry logic
  - `.env` - Add QDRANT_CLUSTER_ENDPOINT and QDRANT_API_KEY
- **Breaking changes**: None - API contracts unchanged
- **User impact**: Better reliability (99.9% SLA), automatic backups, no local infrastructure management
