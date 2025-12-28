"""
OpenAI Rate Limiter

Implements sliding window rate limiting to stay within OpenAI's basic tier limits:
- 3,500 Requests Per Minute (RPM) limit
- Tracks requests across all OpenAI operations
- Provides queuing and delay mechanisms
"""

import time
import logging
from typing import Dict, Tuple, Optional
from collections import deque
from threading import Lock
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window rate limiter for OpenAI API.

    Tracks requests in a time window and prevents exceeding limits.
    Uses exponential backoff for throttled requests.
    """

    def __init__(
        self,
        max_requests_per_minute: int = 3500,
        window_seconds: int = 60,
        burst_size: int = 10,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_minute: Max RPM (3500 for OpenAI basic tier)
            window_seconds: Time window for calculating RPM (default 60s)
            burst_size: Max requests allowed in burst (default 10)
        """
        self.max_rpm = max_requests_per_minute
        self.window_seconds = window_seconds
        self.burst_size = burst_size
        self.requests: deque = deque()  # (timestamp, service_name)
        self.lock = Lock()
        self.last_request_time: float = 0

        # Calculate ideal delay between requests
        self.min_delay_seconds = (window_seconds / max_requests_per_minute) * 1.1  # 10% buffer

        logger.info(
            f"RateLimiter initialized: {max_requests_per_minute} RPM, "
            f"min_delay: {self.min_delay_seconds:.3f}s"
        )

    def can_make_request(self) -> bool:
        """Check if request can be made without exceeding limits."""
        with self.lock:
            now = time.time()
            # Remove old requests outside window
            while self.requests and self.requests[0][0] < now - self.window_seconds:
                self.requests.popleft()

            return len(self.requests) < self.max_rpm

    def acquire(self, service_name: str = "unknown") -> float:
        """
        Acquire permission to make a request.

        Blocks/delays if necessary to maintain rate limit.

        Args:
            service_name: Name of service making request (for tracking)

        Returns:
            Delay in seconds before request can be made
        """
        with self.lock:
            now = time.time()

            # Remove old requests
            while self.requests and self.requests[0][0] < now - self.window_seconds:
                self.requests.popleft()

            current_count = len(self.requests)

            # Check if we can make request immediately
            if current_count < self.max_rpm:
                self.requests.append((now, service_name))
                return 0

            # Calculate delay using exponential backoff
            time_until_oldest_expires = self.requests[0][0] + self.window_seconds - now
            if time_until_oldest_expires < 0:
                time_until_oldest_expires = 0

            # Add small random jitter to prevent thundering herd
            delay = max(time_until_oldest_expires + 0.001, self.min_delay_seconds)

            logger.warning(
                f"Rate limit approached ({current_count}/{self.max_rpm}). "
                f"Delaying {delay:.3f}s for {service_name}"
            )

            return delay

    def request(self, service_name: str = "unknown") -> float:
        """
        Make a rate-limited request.

        Handles delay if needed.

        Args:
            service_name: Name of service making request

        Returns:
            Actual delay applied in seconds
        """
        delay = self.acquire(service_name)
        if delay > 0:
            logger.debug(f"Sleeping {delay:.3f}s for rate limiting ({service_name})")
            time.sleep(delay)
        return delay

    def get_stats(self) -> Dict[str, any]:
        """Get current rate limiter statistics."""
        with self.lock:
            now = time.time()
            # Count requests in last minute
            recent = sum(1 for t, _ in self.requests if t > now - self.window_seconds)

            return {
                "current_rpm": recent,
                "max_rpm": self.max_rpm,
                "utilization_percent": (recent / self.max_rpm * 100) if self.max_rpm > 0 else 0,
                "total_tracked": len(self.requests),
                "min_delay_seconds": self.min_delay_seconds,
                "timestamp": datetime.now().isoformat(),
            }

    def reset(self):
        """Reset rate limiter (for testing)."""
        with self.lock:
            self.requests.clear()
            self.last_request_time = 0
        logger.info("RateLimiter reset")


class ServiceRateLimiter:
    """
    Track rate limits per service (embeddings, metadata, chain).
    """

    def __init__(self, max_rpm: int = 3500):
        """
        Initialize service-level rate limiter.

        Args:
            max_rpm: Max requests per minute across all services
        """
        self.global_limiter = RateLimiter(max_requests_per_minute=max_rpm)
        self.service_limits: Dict[str, RateLimiter] = {}
        self.lock = Lock()

        logger.info(f"ServiceRateLimiter initialized with {max_rpm} global RPM")

    def get_service_limiter(self, service_name: str) -> RateLimiter:
        """Get or create limiter for specific service."""
        with self.lock:
            if service_name not in self.service_limits:
                # Services share the global limit
                self.service_limits[service_name] = self.global_limiter
            return self.service_limits[service_name]

    def request(self, service_name: str) -> float:
        """Request rate-limited slot for service."""
        limiter = self.get_service_limiter(service_name)
        return limiter.request(service_name)

    def get_stats(self) -> Dict[str, any]:
        """Get detailed statistics."""
        stats = {
            "global": self.global_limiter.get_stats(),
            "services": {},
            "timestamp": datetime.now().isoformat(),
        }

        with self.lock:
            for service_name, limiter in self.service_limits.items():
                stats["services"][service_name] = limiter.get_stats()

        return stats


# Global instance
_rate_limiter: Optional[ServiceRateLimiter] = None


def get_rate_limiter() -> ServiceRateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = ServiceRateLimiter(max_rpm=10)  # Custom RPM limit
    return _rate_limiter


def initialize_rate_limiter(max_rpm: int = 10) -> ServiceRateLimiter:
    """Initialize rate limiter with custom settings."""
    global _rate_limiter
    _rate_limiter = ServiceRateLimiter(max_rpm=max_rpm)
    return _rate_limiter
