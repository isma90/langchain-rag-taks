"""
Production-Ready Caching Layer with Redis

Provides high-performance caching for RAG queries and embeddings.
Includes TTL management, async operations, and cache invalidation.
"""

import redis
import json
import hashlib
from typing import Optional, Any, Callable
from datetime import timedelta
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class ProductionCache:
    """Production-ready caching with Redis"""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.default_ttl = default_ttl
            logger.info(f"Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            self.redis_client = None
            raise

    def _make_key(self, prefix: str, data: dict) -> str:
        """
        Generate cache key from prefix and data.

        Uses MD5 hash for deterministic, consistent keys.

        Args:
            prefix: Cache key prefix (e.g., 'rag_query', 'embedding')
            data: Dictionary to hash (e.g., {'query': 'What is AI?'})

        Returns:
            Cache key (e.g., 'rag_query:5d41402abc4b2a76b9719d911017c592')
        """
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{data_hash}"

    def get(self, prefix: str, query_data: dict) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            prefix: Cache key prefix
            query_data: Data to use for key generation

        Returns:
            Cached value or None if not found/expired
        """
        if not self.redis_client:
            return None

        try:
            key = self._make_key(prefix, query_data)
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache HIT: {prefix}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: {prefix}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(self, prefix: str, query_data: dict, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache with TTL.

        Args:
            prefix: Cache key prefix
            query_data: Data to use for key generation
            value: Value to cache
            ttl: Time-to-live in seconds (default: self.default_ttl)
        """
        if not self.redis_client:
            return

        try:
            key = self._make_key(prefix, query_data)
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {prefix} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def delete(self, prefix: str, query_data: dict):
        """
        Delete specific cached value.

        Args:
            prefix: Cache key prefix
            query_data: Data to use for key generation
        """
        if not self.redis_client:
            return

        try:
            key = self._make_key(prefix, query_data)
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {prefix}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern (use carefully!).

        Args:
            pattern: Pattern to match (e.g., 'rag_query:*')
        """
        if not self.redis_client:
            return

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cache invalidated: {len(keys)} keys matching {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")

    def clear_all(self):
        """Clear entire cache (use with caution in production!)"""
        if not self.redis_client:
            return

        try:
            self.redis_client.flushdb()
            logger.warning("Cache cleared completely")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")

    async def async_get(self, prefix: str, query_data: dict) -> Optional[Any]:
        """Async cache get (runs in thread pool)"""
        return await asyncio.to_thread(self.get, prefix, query_data)

    async def async_set(self, prefix: str, query_data: dict, value: Any, ttl: Optional[int] = None):
        """Async cache set (runs in thread pool)"""
        return await asyncio.to_thread(self.set, prefix, query_data, value, ttl)

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.redis_client:
            return {'status': 'offline'}

        try:
            info = self.redis_client.info()
            return {
                'status': 'online',
                'memory_used': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_keys': self.redis_client.dbsize(),
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {'status': 'error', 'error': str(e)}


def cache_result(
    cache: ProductionCache,
    prefix: str = 'result',
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorator to cache function results.

    Usage:
        cache = ProductionCache('redis://localhost:6379')

        @cache_result(cache, prefix='expensive_query', ttl=3600)
        def expensive_computation(param1, param2):
            return "result"

        result = expensive_computation(param1=value1, param2=value2)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function args
            cache_data = {'args': args, 'kwargs': kwargs}

            # Try to get from cache
            cached = cache.get(prefix, cache_data)
            if cached is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached

            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(prefix, cache_data, result, ttl=ttl)
            logger.debug(f"Cache SET for {func.__name__}")

            return result

        return wrapper

    return decorator


# Singleton instance
_cache_instance: Optional[ProductionCache] = None


def get_cache(redis_url: str = 'redis://localhost:6379') -> ProductionCache:
    """
    Get or create cache instance (singleton).

    Args:
        redis_url: Redis connection URL

    Returns:
        ProductionCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ProductionCache(redis_url)
    return _cache_instance
