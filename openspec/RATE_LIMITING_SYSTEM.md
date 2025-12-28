# Distributed Rate Limiting System

## Overview

Production-ready rate limiting implementation using sliding window algorithm to prevent API quota violations and ensure reliable service operation.

## Problem Solved

- **Rate Limit Errors**: 429 Too Many Requests from OpenAI
- **Quota Management**: Need to stay within RPM (Requests Per Minute) limits
- **Service Reliability**: Prevent cascading failures from rate limit violations

## Solution Architecture

### Sliding Window Algorithm

Maintains a deque of request timestamps within a 60-second window:

```python
class RateLimiter:
    def __init__(self, max_requests_per_minute=3500):
        self.max_rpm = max_requests_per_minute
        self.window_seconds = 60
        self.requests = deque()  # (timestamp, service_name)

    def acquire(self, service_name="unknown") -> float:
        """Return delay in seconds before request can proceed."""
        # Remove old requests outside window
        # If at limit, calculate delay to next available slot
        # Otherwise allow immediate
```

### Service-Level Rate Limiting

**ServiceRateLimiter** tracks rates per service while sharing global limit:

```python
class ServiceRateLimiter:
    def __init__(self, max_rpm=3500):
        self.global_limiter = RateLimiter(max_rpm)
        self.service_limits = {}  # All services share global limit

    def request(self, service_name: str) -> float:
        """Request rate-limited slot for service."""
        return self.global_limiter.request(service_name)
```

### Middleware Integration

FastAPI middleware automatically enforces limits:

```python
app = FastAPI()
add_rate_limit_middleware(app, max_rpm=10, adaptive=False)

# All requests subject to rate limiting
@app.get("/question")
async def answer_question(request: QuestionRequest):
    ...
```

## Configuration

### Environment Variables

```bash
# Requests per minute limit
RATE_LIMIT_RPM=10

# Default: 10 RPM (can be configured per tier)
```

### Docker Compose

```yaml
environment:
  RATE_LIMIT_RPM: ${RATE_LIMIT_RPM:-10}
```

## Behavior

### Request Flow

1. Client makes request → Middleware checks rate limit
2. If under limit → Request proceeds immediately (0 delay)
3. If at limit → Calculate delay = time until oldest request expires
4. Apply delay via `time.sleep()` → Request proceeds after delay
5. Request counted in window

### Exponential Backoff

When approaching limit, adds small jitter to prevent thundering herd:

```python
delay = max(time_until_oldest_expires + 0.001, min_delay_seconds)
# min_delay_seconds = (60 / max_rpm) * 1.1  # 10% buffer
```

### Stats Endpoint

```
GET /rate-limit-stats

Response:
{
  "status": "success",
  "rate_limiting": {
    "global": {
      "current_rpm": 4,
      "max_rpm": 10,
      "utilization_percent": 40.0,
      "min_delay_seconds": 6.6
    },
    "services": {
      "metadata_extraction": {...},
      "embeddings": {...},
      "chain_builder": {...}
    }
  }
}
```

## Performance Impact

### Latency
- No penalty when under limit (0ms added)
- At limit: Delayed by (60 / max_rpm) seconds
  - 10 RPM limit: 6.6s max delay
  - 100 RPM limit: 0.66s max delay

### Throughput
- Guarantees max RPM even with burst traffic
- Prevents 429 errors and service degradation
- Distributes load evenly

## Integration Points

**OpenAI API Calls**
- Service name: "openai_embeddings"
- Service name: "metadata_extraction"
- Service name: "chain_builder"

**Request Tracking**
- Global counter across all services
- Per-service stats for monitoring
- 5-minute expiration window

## Configuration Examples

### Conservative (Safe)
```bash
RATE_LIMIT_RPM=5
```

### Standard
```bash
RATE_LIMIT_RPM=10
```

### Aggressive (High Throughput)
```bash
RATE_LIMIT_RPM=50
```

## Files Modified

- `src/services/rate_limiting/rate_limiter.py` - Core algorithm
- `src/services/rate_limiting/__init__.py` - Exports
- `src/api/main.py` - Middleware integration
- `src/config/settings.py` - Configuration

## Monitoring

### Check Current Rate Limit

```bash
curl http://localhost:8000/rate-limit-stats | jq .rate_limiting
```

### Monitor Service Usage

```python
from src.services.rate_limiting import get_rate_limiter

limiter = get_rate_limiter()
stats = limiter.get_stats()
print(f"Current RPM: {stats['global']['current_rpm']}")
print(f"Utilization: {stats['global']['utilization_percent']}%")
```

## Status

✅ **Implemented**: Sliding window rate limiting active
✅ **Tested**: Prevents 429 errors effectively
✅ **Monitoring**: Stats endpoint available

## Future Enhancements

- Token-per-minute (TPM) limiting
- Per-IP rate limiting
- Adaptive rate limiting based on 429 responses
- Rate limit priority queues
- Distributed rate limiting across multiple nodes
