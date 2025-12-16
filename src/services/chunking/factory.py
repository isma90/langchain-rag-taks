"""
Chunking Strategy Factory

Selects and configures the optimal chunking strategy based on content type,
document size, and quality requirements.

CRITICAL: All chunk sizes are in TOKENS, not characters!
"""

from enum import Enum
from typing import Callable, Optional, Tuple, Dict, Any
import logging

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
)
from src.utils.tokenization import get_token_counter

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    MARKDOWN = "markdown"
    HTML = "html"
    PYTHON_CODE = "python_code"
    JSON = "json"


class ChunkingFactory:
    """Factory for creating optimal chunking strategies"""

    def __init__(self, token_counter: Optional[Callable] = None):
        """
        Initialize chunking factory.

        Args:
            token_counter: Token counting function (default: tiktoken for gpt-4o)
        """
        if token_counter is None:
            counter = get_token_counter()
            token_counter = counter.count_tokens

        self.token_counter = token_counter
        logger.info("ChunkingFactory initialized")

    def create_recursive(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        keep_separator: bool = True,
        strip_whitespace: bool = True,
    ) -> RecursiveCharacterTextSplitter:
        """
        Create RecursiveCharacterTextSplitter (recommended for most cases).

        Pattern: Tries multiple separator levels to preserve semantics
        - # ## ### \n\n \n . space

        Args:
            chunk_size: Size of each chunk in TOKENS (not characters!)
            chunk_overlap: Token overlap between chunks (20% recommended)
            keep_separator: Keep separators in output
            strip_whitespace: Strip leading/trailing whitespace

        Returns:
            Configured RecursiveCharacterTextSplitter

        Usage:
            splitter = factory.create_recursive()
            chunks = splitter.split_documents(documents)
        """
        logger.info(
            f"Creating RecursiveCharacterTextSplitter: "
            f"size={chunk_size}, overlap={chunk_overlap}"
        )

        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.token_counter,  # CRITICAL: Use token counting
            separators=[
                "\n# ",      # H1 headers (Markdown)
                "\n## ",     # H2 headers
                "\n### ",    # H3 headers
                "\n\n",      # Paragraph breaks
                "\n",        # Line breaks
                ". ",        # Sentence breaks
                " ",         # Word breaks
                "",          # Character breaks (last resort)
            ],
            keep_separator=keep_separator,
            strip_whitespace=strip_whitespace,
        )

    def create_markdown(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        headers_to_split_on: Optional[list] = None,
    ) -> MarkdownHeaderTextSplitter:
        """
        Create MarkdownHeaderTextSplitter for respecting document structure.

        Pattern: Splits on Markdown headers while preserving hierarchy

        Args:
            chunk_size: Size of each chunk in TOKENS
            chunk_overlap: Token overlap between chunks
            headers_to_split_on: Headers to split on (e.g., [("#", "Header 1"), ("##", "Header 2")])

        Returns:
            Configured MarkdownHeaderTextSplitter

        Usage:
            splitter = factory.create_markdown()
            chunks = splitter.split_text(markdown_text)
        """
        if headers_to_split_on is None:
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]

        logger.info(f"Creating MarkdownHeaderTextSplitter: size={chunk_size}")

        return MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.token_counter,  # CRITICAL: Use token counting
        )

    def create_html(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        headers_to_split_on: Optional[list] = None,
    ) -> HTMLHeaderTextSplitter:
        """
        Create HTMLHeaderTextSplitter for HTML documents.

        Pattern: Respects HTML hierarchy while splitting

        Args:
            chunk_size: Size of each chunk in TOKENS
            chunk_overlap: Token overlap between chunks
            headers_to_split_on: HTML headers to split on

        Returns:
            Configured HTMLHeaderTextSplitter

        Usage:
            splitter = factory.create_html()
            chunks = splitter.split_text(html_text)
        """
        if headers_to_split_on is None:
            headers_to_split_on = [
                ("h1", "Header 1"),
                ("h2", "Header 2"),
                ("h3", "Header 3"),
            ]

        logger.info(f"Creating HTMLHeaderTextSplitter: size={chunk_size}")

        return HTMLHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.token_counter,  # CRITICAL: Use token counting
        )

    def select_optimal(
        self,
        content_type: str,
        document_size: int = 0,
        quality_requirement: str = "standard",
    ) -> Tuple[ChunkingStrategy, Dict[str, Any]]:
        """
        Automatically select optimal strategy and parameters.

        Decision Matrix:
        - Small documents (< 5K tokens): Recursive with larger chunks
        - Markdown: Use MarkdownHeaderTextSplitter
        - HTML: Use HTMLHeaderTextSplitter
        - High quality requirement: SemanticChunker (if available)

        Args:
            content_type: Type of content (markdown, html, python, json, text)
            document_size: Size of document in tokens
            quality_requirement: Quality level (low, standard, high, premium)

        Returns:
            Tuple of (strategy, parameters)

        Usage:
            strategy, params = factory.select_optimal('markdown')
            splitter = factory.create_recursive(**params)
        """
        logger.info(
            f"Selecting optimal strategy for {content_type} "
            f"(size={document_size}, quality={quality_requirement})"
        )

        # Quality-based parameter adjustments
        quality_configs = {
            "low": {
                "chunk_size": 1500,
                "chunk_overlap": 100,
            },
            "standard": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
            },
            "high": {
                "chunk_size": 800,
                "chunk_overlap": 250,
            },
            "premium": {
                "chunk_size": 600,
                "chunk_overlap": 300,
            },
        }

        params = quality_configs.get(quality_requirement, quality_configs["standard"])

        # Content-type specific selection
        content_type_lower = content_type.lower()

        if content_type_lower == "markdown":
            return ChunkingStrategy.MARKDOWN, {
                **params,
                "headers_to_split_on": [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                ],
            }

        elif content_type_lower == "html":
            return ChunkingStrategy.HTML, {
                **params,
                "headers_to_split_on": [
                    ("h1", "Header 1"),
                    ("h2", "Header 2"),
                    ("h3", "Header 3"),
                ],
            }

        elif content_type_lower in ["python", "code", "javascript"]:
            # For code, use smaller chunks with less overlap
            code_params = {
                "chunk_size": 400,
                "chunk_overlap": 50,
            }
            return ChunkingStrategy.RECURSIVE, code_params

        else:
            # Default to recursive for mixed/unknown content
            return ChunkingStrategy.RECURSIVE, params

    def get_recommended_config(
        self,
        content_type: str,
    ) -> Dict[str, Any]:
        """
        Get recommended configuration for content type.

        Args:
            content_type: Type of content

        Returns:
            Dictionary with recommended settings
        """
        strategy, params = self.select_optimal(content_type)

        return {
            "strategy": strategy.value,
            "parameters": params,
            "explanation": self._get_explanation(strategy),
        }

    @staticmethod
    def _get_explanation(strategy: ChunkingStrategy) -> str:
        """Get explanation for chosen strategy"""
        explanations = {
            ChunkingStrategy.RECURSIVE: (
                "RecursiveCharacterTextSplitter respects document structure "
                "by trying multiple separator levels. Good for mixed content."
            ),
            ChunkingStrategy.SEMANTIC: (
                "SemanticChunker uses embeddings to find natural topic boundaries. "
                "Highest quality but more expensive (60-70% more tokens)."
            ),
            ChunkingStrategy.MARKDOWN: (
                "MarkdownHeaderTextSplitter preserves markdown hierarchy. "
                "Best for documentation and technical content."
            ),
            ChunkingStrategy.HTML: (
                "HTMLHeaderTextSplitter respects HTML structure. "
                "Ideal for web content and articles."
            ),
            ChunkingStrategy.PYTHON_CODE: (
                "Code-specific splitting respects function/class boundaries. "
                "Smaller chunks for maintainability."
            ),
            ChunkingStrategy.JSON: (
                "JSON-aware splitting preserves object structure. "
                "Specialized for API responses and structured data."
            ),
        }
        return explanations.get(strategy, "Custom chunking strategy")
