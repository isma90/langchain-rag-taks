"""
FastAPI Rate Limiting Middleware

Applies rate limiting at the HTTP request level to control overall API load.
"""

import logging
import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.services.rate_limiting.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Tracks API requests and applies delays/rejections based on rate limits.
    """

    def __init__(self, app, max_rpm: int = 3500):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            max_rpm: Max requests per minute (3500 for OpenAI basic tier)
        """
        super().__init__(app)
        self.rate_limiter = get_rate_limiter()
        self.max_rpm = max_rpm

        logger.info(f"RateLimitMiddleware initialized: {max_rpm} RPM limit")

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request through rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Get service name from endpoint
        service_name = self._get_service_name(request)

        # Only rate limit OpenAI-related endpoints
        if service_name and self._should_rate_limit(service_name):
            # Request rate-limited slot
            delay = self.rate_limiter.request(service_name)

            # Add rate limit info to response headers
            response = await call_next(request)
            stats = self.rate_limiter.get_stats()

            response.headers["X-RateLimit-Limit"] = str(self.max_rpm)
            response.headers["X-RateLimit-Current"] = str(
                stats["global"]["current_rpm"]
            )
            response.headers["X-RateLimit-Percent"] = str(
                int(stats["global"]["utilization_percent"])
            )

            if delay > 0:
                logger.info(
                    f"Rate limit applied: {service_name} "
                    f"({stats['global']['current_rpm']}/{self.max_rpm} RPM)"
                )

            return response

        # No rate limiting needed
        return await call_next(request)

    def _get_service_name(self, request: Request) -> str:
        """Extract service name from request path."""
        path = request.url.path

        if "/initialize" in path:
            return "initialize"
        elif "/question" in path or "/batch-questions" in path:
            return "question_answering"
        elif "/search" in path:
            return "search"
        elif "/stats" in path:
            return "stats"
        elif "/collection" in path:
            return "collection_management"

        return "unknown"

    def _should_rate_limit(self, service_name: str) -> bool:
        """Determine if service should be rate limited."""
        # Rate limit everything except health check
        return service_name != "health"


class AdaptiveRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Adaptive rate limiting middleware.

    Adjusts rate limit based on system load and error responses.
    """

    def __init__(self, app, initial_rpm: int = 3500, min_rpm: int = 500):
        """
        Initialize adaptive middleware.

        Args:
            app: FastAPI application
            initial_rpm: Starting RPM limit
            min_rpm: Minimum RPM allowed
        """
        super().__init__(app)
        self.current_rpm = initial_rpm
        self.min_rpm = min_rpm
        self.max_rpm = initial_rpm
        self.rate_limiter = get_rate_limiter()
        self.consecutive_errors = 0
        self.last_adjustment = time.time()

        logger.info(f"AdaptiveRateLimitMiddleware initialized: {initial_rpm} RPM")

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request with adaptive rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        start_time = time.time()
        service_name = self._get_service_name(request)

        # Rate limit if needed
        if service_name and self._should_rate_limit(service_name):
            delay = self.rate_limiter.request(service_name)

        # Call next middleware
        response = await call_next(request)

        # Check response status
        response_time = (time.time() - start_time) * 1000

        if response.status_code >= 429:
            # Rate limit error - reduce RPM
            self.consecutive_errors += 1
            self._adjust_rate_limit(reduce=True)
        elif response.status_code >= 500:
            # Server error - reduce RPM
            self.consecutive_errors += 1
            self._adjust_rate_limit(reduce=True)
        else:
            # Success - reset error counter
            self.consecutive_errors = 0

        # Add adaptive info to headers
        response.headers["X-RateLimit-Current-RPM"] = str(self.current_rpm)
        response.headers["X-Response-Time-Ms"] = str(int(response_time))

        return response

    def _get_service_name(self, request: Request) -> str:
        """Extract service name from request path."""
        path = request.url.path

        if "/initialize" in path:
            return "initialize"
        elif "/question" in path or "/batch-questions" in path:
            return "question_answering"
        elif "/search" in path:
            return "search"

        return "unknown"

    def _should_rate_limit(self, service_name: str) -> bool:
        """Determine if service should be rate limited."""
        return service_name != "health"

    def _adjust_rate_limit(self, reduce: bool = False):
        """Adjust rate limit based on errors."""
        now = time.time()

        # Only adjust once per 5 seconds
        if now - self.last_adjustment < 5:
            return

        if reduce and self.consecutive_errors >= 3:
            # Reduce RPM by 20%
            new_rpm = int(self.current_rpm * 0.8)
            if new_rpm >= self.min_rpm:
                self.current_rpm = new_rpm
                logger.warning(
                    f"Reducing rate limit to {self.current_rpm} RPM "
                    f"(due to {self.consecutive_errors} consecutive errors)"
                )
                self.last_adjustment = now


def add_rate_limit_middleware(app, max_rpm: int = 3500, adaptive: bool = False):
    """
    Add rate limiting middleware to FastAPI app.

    Args:
        app: FastAPI application
        max_rpm: Max requests per minute
        adaptive: Use adaptive rate limiting
    """
    if adaptive:
        app.add_middleware(AdaptiveRateLimitMiddleware, initial_rpm=max_rpm)
        logger.info("Added AdaptiveRateLimitMiddleware")
    else:
        app.add_middleware(RateLimitMiddleware, max_rpm=max_rpm)
        logger.info("Added RateLimitMiddleware")
