"""
Token Counting Utilities

Critical for chunking: Uses tiktoken (same as OpenAI) to count tokens.
NEVER use character counts - always use token counts in production!
"""

import tiktoken
from functools import lru_cache
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token counting utility using tiktoken (2025 standard)"""

    def __init__(self, model: str = 'gpt-4o'):
        """
        Initialize token counter for specific model.

        Args:
            model: Model name (gpt-4o, gpt-3.5-turbo, text-embedding-3-large, etc.)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
            self.model = model
            logger.info(f"Initialized TokenCounter for model: {model}")
        except Exception as e:
            logger.warning(f"Failed to load encoding for {model}, falling back to cl100k_base: {e}")
            self.encoding = tiktoken.get_encoding('cl100k_base')
            self.model = model

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        This is CRITICAL for chunking - use this for ALL chunk size calculations,
        never use character counts!

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Example:
            token_counter = TokenCounter()
            tokens = token_counter.count_tokens("Hello world")  # 2
        """
        try:
            tokens = len(self.encoding.encode(text))
            return tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def count_tokens_from_messages(self, messages: list) -> int:
        """
        Count tokens from a list of messages (OpenAI format).

        Args:
            messages: List of dicts with 'role' and 'content' keys

        Returns:
            Total tokens including overhead
        """
        total_tokens = 0
        for message in messages:
            total_tokens += 4  # Message overhead
            for key, value in message.items():
                total_tokens += len(self.encoding.encode(str(value)))
        total_tokens += 2  # Response overhead
        return total_tokens

    def estimate_cost(
        self,
        tokens: int,
        model: str = 'text-embedding-3-large',
        direction: str = 'embedding'
    ) -> float:
        """
        Estimate API cost for tokens.

        Args:
            tokens: Number of tokens
            model: Model name
            direction: 'embedding' or 'completion'

        Returns:
            Estimated cost in USD
        """
        # 2025 pricing
        prices = {
            'text-embedding-3-small': 0.00002,
            'text-embedding-3-large': 0.00013,
            'gpt-4o-mini': 0.00015,
            'gpt-4o': 0.03,  # Input only (approx)
        }
        price_per_1k = prices.get(model, 0.00013)
        return (tokens / 1000) * price_per_1k

    def is_within_limit(self, text: str, max_tokens: int) -> bool:
        """
        Check if text is within token limit.

        Args:
            text: Text to check
            max_tokens: Maximum tokens allowed

        Returns:
            True if within limit, False otherwise
        """
        return self.count_tokens(text) <= max_tokens

    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens

        Returns:
            Truncated text
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

    def split_into_chunks(
        self,
        text: str,
        chunk_size: int,
        overlap: int = 200
    ) -> list:
        """
        Split text into fixed-size token chunks with overlap.

        Args:
            text: Text to split
            chunk_size: Size of each chunk in tokens
            overlap: Token overlap between chunks

        Returns:
            List of text chunks
        """
        tokens = self.encoding.encode(text)
        chunks = []

        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i : i + chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks

    def get_stats(self, text: str) -> dict:
        """
        Get detailed token statistics for text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with token statistics
        """
        tokens = self.encoding.encode(text)
        return {
            'total_tokens': len(tokens),
            'characters': len(text),
            'words': len(text.split()),
            'lines': len(text.split('\n')),
            'avg_chars_per_token': len(text) / len(tokens) if tokens else 0,
            'avg_tokens_per_word': len(tokens) / len(text.split()) if text.split() else 0,
        }


# Singleton instance for efficiency
@lru_cache(maxsize=1)
def get_token_counter(model: str = 'gpt-4o') -> TokenCounter:
    """Get or create token counter (cached)"""
    return TokenCounter(model)


# Default instance
default_token_counter = get_token_counter()


def count_tokens(text: str, model: str = 'gpt-4o') -> int:
    """
    Quick function to count tokens.

    Usage:
        from src.utils.tokenization import count_tokens
        tokens = count_tokens("Hello world")
    """
    counter = get_token_counter(model)
    return counter.count_tokens(text)


def estimate_cost(
    tokens: int,
    model: str = 'text-embedding-3-large'
) -> float:
    """Quick function to estimate cost"""
    return default_token_counter.estimate_cost(tokens, model)


# ============================================================================
# Integration with LangChain TextSplitters
# ============================================================================

def create_token_counter_func(model: str = 'gpt-4o'):
    """
    Create a token counter function for use with LangChain splitters.

    Usage:
        from src.utils.tokenization import create_token_counter_func
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        token_counter = create_token_counter_func()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=token_counter,  # ← Use here
        )
    """
    counter = get_token_counter(model)
    return counter.count_tokens
