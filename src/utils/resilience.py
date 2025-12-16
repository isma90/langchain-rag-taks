"""
Resilience Patterns: Retry Logic & Circuit Breaker

Provides production-ready patterns for handling failures and cascading failures
in external API calls (OpenAI, Qdrant, etc.)
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class APICircuitBreaker:
    """
    Production-ready circuit breaker for external API calls.

    Pattern: Fail Fast & Prevent Cascading Failures

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Attempting recovery with limited requests
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery (HALF_OPEN)
            success_threshold: Successful calls needed to close circuit from HALF_OPEN
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()

        logger.info(
            f"Circuit breaker initialized: "
            f"threshold={failure_threshold}, "
            f"timeout={recovery_timeout}s"
        )

    def _attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return False

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure > timedelta(seconds=self.recovery_timeout)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Handle OPEN state
        if self.state == CircuitState.OPEN:
            if self._attempt_recovery():
                logger.info("Circuit breaker: Attempting recovery (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. "
                    f"Service unavailable. "
                    f"Retry in {self.recovery_timeout}s"
                )

        # Execute function
        try:
            result = func(*args, **kwargs)

            # Handle success in HALF_OPEN state
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("Circuit breaker: CLOSED (recovered)")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.critical(
                    f"Circuit breaker OPEN after {self.failure_count} failures"
                )

            raise

    def get_state(self) -> dict:
        """Get circuit breaker state information"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_state_change': self.last_state_change.isoformat(),
        }


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for automatic retries with exponential backoff.

    Pattern: Retry transient failures with increasing delays

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Exceptions that trigger retry

    Usage:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def flaky_api_call():
            return api.call()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Max retries exceeded ({max_attempts}) for {func.__name__}: {e}"
                        )
                        raise

                    # Calculate backoff with optional jitter
                    backoff = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
                    if jitter:
                        import random
                        backoff *= (0.5 + random.random())  # Jitter: 50-150% of backoff

                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {backoff:.2f}s: {e}"
                    )

                    time.sleep(backoff)

            # Should not reach here, but just in case
            raise last_exception

        return wrapper

    return decorator


class RateLimiter:
    """
    Simple rate limiter using token bucket algorithm.

    Prevents excessive API calls and distributes load smoothly.
    """

    def __init__(self, max_calls: int, time_window: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.call_times = []
        logger.info(f"Rate limiter initialized: {max_calls} calls per {time_window}s")

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove old calls outside the window
        self.call_times = [t for t in self.call_times if now - t < self.time_window]

        # If at limit, wait
        if len(self.call_times) >= self.max_calls:
            sleep_time = self.time_window - (now - self.call_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            self.call_times = []  # Reset

        self.call_times.append(now)

    def is_allowed(self) -> bool:
        """Check if call is allowed without waiting"""
        now = time.time()
        self.call_times = [t for t in self.call_times if now - t < self.time_window]
        return len(self.call_times) < self.max_calls


class TokenRateLimiter:
    """
    Rate limit based on token consumption (for OpenAI API).

    Tracks token usage and prevents exceeding rate limits.
    """

    def __init__(self, tokens_per_minute: int = 90000):
        """
        Initialize token rate limiter.

        Args:
            tokens_per_minute: Token budget per minute (OpenAI default: 90K)
        """
        self.tokens_per_minute = tokens_per_minute
        self.tokens_used_in_window = 0
        self.last_reset = datetime.now()
        logger.info(f"Token rate limiter: {tokens_per_minute} tokens/minute")

    def is_allowed(self, tokens_required: int) -> bool:
        """
        Check if request with given tokens is allowed.

        Args:
            tokens_required: Number of tokens the request will use

        Returns:
            True if allowed, False if would exceed limit
        """
        now = datetime.now()
        elapsed = (now - self.last_reset).total_seconds()

        # Reset window if minute has passed
        if elapsed > 60:
            self.tokens_used_in_window = 0
            self.last_reset = now
            elapsed = 0

        # Check if request fits in budget
        if self.tokens_used_in_window + tokens_required <= self.tokens_per_minute:
            self.tokens_used_in_window += tokens_required
            return True

        return False

    def wait_if_needed(self, tokens_required: int):
        """
        Block until tokens are available.

        Args:
            tokens_required: Number of tokens needed
        """
        while not self.is_allowed(tokens_required):
            sleep_time = max(0.1, 60 - (datetime.now() - self.last_reset).total_seconds())
            logger.debug(f"Token limit approaching, waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def get_status(self) -> dict:
        """Get current token usage status"""
        elapsed = (datetime.now() - self.last_reset).total_seconds()
        return {
            'tokens_used': self.tokens_used_in_window,
            'tokens_available': self.tokens_per_minute,
            'usage_percent': (self.tokens_used_in_window / self.tokens_per_minute) * 100,
            'time_until_reset': max(0, 60 - elapsed),
        }
