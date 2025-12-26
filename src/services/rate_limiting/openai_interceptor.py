"""
OpenAI API Interceptor

Wraps OpenAI clients to apply rate limiting before each request.
Integrates seamlessly with LangChain's ChatOpenAI and OpenAIEmbeddings.
"""

import logging
import functools
from typing import Any, Callable
from src.services.rate_limiting.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


class OpenAIRateLimitInterceptor:
    """
    Intercepts OpenAI API calls to apply rate limiting.

    Usage:
        interceptor = OpenAIRateLimitInterceptor()

        # For ChatOpenAI
        llm = ChatOpenAI(...)
        llm_limited = interceptor.wrap_chat_openai(llm, service_name="chat")

        # For OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(...)
        embeddings_limited = interceptor.wrap_embeddings(embeddings, service_name="embeddings")
    """

    def __init__(self):
        """Initialize interceptor."""
        self.rate_limiter = get_rate_limiter()
        logger.info("OpenAIRateLimitInterceptor initialized")

    def apply_rate_limit(self, service_name: str) -> Callable:
        """
        Decorator that applies rate limiting to a method.

        Args:
            service_name: Name of service being rate limited

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Apply rate limit
                delay = self.rate_limiter.request(service_name)

                # Log if delay was applied
                if delay > 0:
                    logger.debug(f"Rate limited {service_name}: waited {delay:.3f}s")

                # Call original function
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def wrap_chat_openai(self, llm: Any, service_name: str = "chat_openai") -> Any:
        """
        Wrap ChatOpenAI client with rate limiting.

        Args:
            llm: ChatOpenAI instance
            service_name: Name for tracking

        Returns:
            Wrapped instance
        """
        # Wrap the invoke method
        original_invoke = llm.invoke

        @functools.wraps(original_invoke)
        def rate_limited_invoke(*args, **kwargs):
            delay = self.rate_limiter.request(service_name)
            return original_invoke(*args, **kwargs)

        llm.invoke = rate_limited_invoke

        # Also wrap async invoke if available
        if hasattr(llm, "ainvoke"):
            original_ainvoke = llm.ainvoke

            async def rate_limited_ainvoke(*args, **kwargs):
                delay = self.rate_limiter.request(service_name)
                return await original_ainvoke(*args, **kwargs)

            llm.ainvoke = rate_limited_ainvoke

        logger.info(f"Wrapped ChatOpenAI with rate limiting: {service_name}")
        return llm

    def wrap_embeddings(self, embeddings: Any, service_name: str = "embeddings") -> Any:
        """
        Wrap OpenAIEmbeddings client with rate limiting.

        Args:
            embeddings: OpenAIEmbeddings instance
            service_name: Name for tracking

        Returns:
            Wrapped instance
        """
        # Wrap the embed_documents method
        original_embed = embeddings.embed_documents

        def rate_limited_embed(texts):
            delay = self.rate_limiter.request(service_name)
            return original_embed(texts)

        embeddings.embed_documents = rate_limited_embed

        # Wrap embed_query
        if hasattr(embeddings, "embed_query"):
            original_embed_query = embeddings.embed_query

            def rate_limited_embed_query(text):
                delay = self.rate_limiter.request(service_name)
                return original_embed_query(text)

            embeddings.embed_query = rate_limited_embed_query

        logger.info(f"Wrapped OpenAIEmbeddings with rate limiting: {service_name}")
        return embeddings

    def get_stats(self):
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()


# Global interceptor instance
_interceptor = None


def get_interceptor() -> OpenAIRateLimitInterceptor:
    """Get or create global interceptor."""
    global _interceptor
    if _interceptor is None:
        _interceptor = OpenAIRateLimitInterceptor()
    return _interceptor
