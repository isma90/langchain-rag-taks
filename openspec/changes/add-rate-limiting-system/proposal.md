# Change: Add Rate Limiting System

## Why

The system makes requests to OpenAI API which has strict rate limits (3,500 RPM for basic tier). Without rate limiting, burst traffic would cause 429 "Too Many Requests" errors, degrading service reliability and wasting API quota.

## What Changes

- Implement sliding window rate limiting algorithm to track request timestamps
- Add FastAPI middleware to enforce rate limits on all endpoints
- Create `/rate-limit-stats` endpoint to monitor current usage
- Support configurable RPM (requests per minute) via environment variable
- Track per-service request counts for detailed monitoring

## Impact

- **Affected specs**: `api-reliability`
- **Affected code**:
  - `src/services/rate_limiting/rate_limiter.py` - New rate limiter implementation
  - `src/api/main.py:140` - Middleware registration
  - `src/api/main.py:541-569` - Stats endpoint
  - `src/config/settings.py` - Configuration fields
  - `docker-compose.yml` - RATE_LIMIT_RPM env variable
- **Breaking changes**: None - rate limiting is transparent to clients
- **User impact**: Improved reliability, prevents API quota violations, automatic delays when necessary
