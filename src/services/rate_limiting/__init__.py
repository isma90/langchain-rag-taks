"""
OpenAI Rate Limiting Control System

Complete rate limiting implementation for OpenAI API (3,500 RPM basic tier).

Components:
1. RateLimiter - Sliding window rate limiting algorithm
2. ServiceRateLimiter - Per-service rate limit tracking
3. OpenAIRateLimitInterceptor - Integration with LangChain clients
4. RateLimitMiddleware - FastAPI HTTP-level rate limiting
5. AdaptiveRateLimitMiddleware - Adaptive rate limiting based on errors

Usage:

Basic rate limiting:
    from src.services.rate_limiting import get_rate_limiter
    limiter = get_rate_limiter()
    limiter.request("service_name")

With LangChain:
    from src.services.rate_limiting import get_interceptor
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(...)
    interceptor = get_interceptor()
    llm = interceptor.wrap_chat_openai(llm, "my_service")

In FastAPI:
    from src.services.rate_limiting import add_rate_limit_middleware

    app = FastAPI()
    add_rate_limit_middleware(app, max_rpm=3500, adaptive=False)

Statistics:
    stats = limiter.get_stats()
    print(f"Current RPM: {stats['global']['current_rpm']}/{stats['global']['max_rpm']}")
    print(f"Utilization: {stats['global']['utilization_percent']}%")
"""

from src.services.rate_limiting.rate_limiter import (
    RateLimiter,
    ServiceRateLimiter,
    get_rate_limiter,
    initialize_rate_limiter,
)
from src.services.rate_limiting.openai_interceptor import (
    OpenAIRateLimitInterceptor,
    get_interceptor,
)
from src.services.rate_limiting.middleware import (
    RateLimitMiddleware,
    AdaptiveRateLimitMiddleware,
    add_rate_limit_middleware,
)

__all__ = [
    # Rate limiter
    "RateLimiter",
    "ServiceRateLimiter",
    "get_rate_limiter",
    "initialize_rate_limiter",
    # Interceptor
    "OpenAIRateLimitInterceptor",
    "get_interceptor",
    # Middleware
    "RateLimitMiddleware",
    "AdaptiveRateLimitMiddleware",
    "add_rate_limit_middleware",
]
