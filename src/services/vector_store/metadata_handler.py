"""
Metadata Handler

Enriches document chunks with extracted metadata using LLM.
Includes: summary, keywords, topic, complexity level, etc.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentMetadata(BaseModel):
    """Structured metadata extracted from document"""
    summary: str = Field(description="1-2 sentence summary")
    keywords: List[str] = Field(description="5-10 relevant keywords")
    topic: str = Field(description="Main topic/category")
    complexity: str = Field(description="easy, medium, or hard")
    entities: List[str] = Field(description="Named entities (people, places, concepts)")
    sentiment: str = Field(description="positive, neutral, or negative")


class MetadataHandler:
    """
    Production-ready metadata extraction and enrichment.

    Uses LLM with structured output to extract metadata from chunks.
    Adds semantic information for better retrieval and filtering.
    """

    def __init__(self, use_structured_output: bool = True):
        """
        Initialize metadata handler.

        Args:
            use_structured_output: Use LLM structured output (Pydantic)
        """
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,  # Deterministic for consistency
            api_key=settings.openai_api_key,
            max_retries=3,  # Retry on rate limit (429) with exponential backoff
        )

        # Use structured output if available
        if use_structured_output:
            self.llm = self.llm.with_structured_output(DocumentMetadata)

        self.use_structured_output = use_structured_output

        logger.info("MetadataHandler initialized")

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text chunk.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with extracted metadata
        """
        prompt = ChatPromptTemplate.from_template("""
Analyze the following text and extract metadata:

TEXT:
{text}

Extract:
1. A 1-2 sentence summary
2. 5-10 relevant keywords
3. Main topic/category
4. Complexity level (easy, medium, hard)
5. Named entities (people, places, important concepts)
6. Overall sentiment (positive, neutral, negative)

Be concise and factual.
""")

        try:
            chain = prompt | self.llm
            result = chain.invoke({"text": text[:1000]})  # Limit to first 1000 chars

            if self.use_structured_output:
                # Already structured
                return result.model_dump()
            else:
                # Parse unstructured response
                return self._parse_unstructured_response(result)

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            # Return default metadata
            return self._get_default_metadata()

    def enrich_documents(
        self,
        documents: List[Document],
        batch_size: int = 10,
    ) -> List[Document]:
        """
        Enrich documents with extracted metadata.

        Args:
            documents: Documents to enrich
            batch_size: Process in batches to manage API calls

        Returns:
            Documents with added metadata
        """
        logger.info(f"Enriching {len(documents)} documents with metadata")

        enriched = []
        for i, doc in enumerate(documents):
            try:
                metadata = self.extract_metadata(doc.page_content)

                # Add extracted metadata to document
                doc.metadata.update({
                    "extracted_summary": metadata.get("summary"),
                    "keywords": metadata.get("keywords", []),
                    "topic": metadata.get("topic"),
                    "complexity": metadata.get("complexity"),
                    "entities": metadata.get("entities", []),
                    "sentiment": metadata.get("sentiment"),
                    "metadata_extracted_at": datetime.utcnow().isoformat(),
                })

                enriched.append(doc)

                if (i + 1) % batch_size == 0:
                    logger.debug(f"Enriched {i + 1}/{len(documents)} documents")

            except Exception as e:
                logger.warning(f"Failed to enrich document {i}: {e}")
                enriched.append(doc)  # Add original without enrichment

        logger.info(f"Enrichment complete: {len(enriched)} documents")
        return enriched

    def filter_by_topic(
        self,
        documents: List[Document],
        topic: str,
    ) -> List[Document]:
        """
        Filter documents by extracted topic.

        Args:
            documents: Documents to filter
            topic: Topic to filter by

        Returns:
            Filtered documents
        """
        filtered = [
            doc for doc in documents
            if doc.metadata.get("topic", "").lower() == topic.lower()
        ]
        logger.info(f"Filtered to {len(filtered)} documents with topic '{topic}'")
        return filtered

    def filter_by_complexity(
        self,
        documents: List[Document],
        min_level: str = "easy",
        max_level: str = "hard",
    ) -> List[Document]:
        """
        Filter documents by complexity level.

        Args:
            documents: Documents to filter
            min_level: Minimum complexity (easy, medium, hard)
            max_level: Maximum complexity

        Returns:
            Filtered documents
        """
        complexity_order = {"easy": 0, "medium": 1, "hard": 2}
        min_val = complexity_order.get(min_level, 0)
        max_val = complexity_order.get(max_level, 2)

        filtered = [
            doc for doc in documents
            if min_val <= complexity_order.get(doc.metadata.get("complexity", "easy"), 0) <= max_val
        ]

        logger.info(f"Filtered to {len(filtered)} documents by complexity")
        return filtered

    def get_keywords_index(
        self,
        documents: List[Document],
    ) -> Dict[str, List[int]]:
        """
        Build keyword index for fast lookup.

        Args:
            documents: Documents with extracted keywords

        Returns:
            Dictionary mapping keywords to document indices
        """
        index = {}
        for i, doc in enumerate(documents):
            keywords = doc.metadata.get("keywords", [])
            for keyword in keywords:
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(i)

        logger.info(f"Built keyword index with {len(index)} unique keywords")
        return index

    def get_statistics(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about extracted metadata.

        Args:
            documents: Documents with metadata

        Returns:
            Statistics dictionary
        """
        topics = {}
        complexities = {"easy": 0, "medium": 0, "hard": 0}
        sentiments = {}
        total_keywords = 0

        for doc in documents:
            # Count topics
            topic = doc.metadata.get("topic", "unknown")
            topics[topic] = topics.get(topic, 0) + 1

            # Count complexity
            complexity = doc.metadata.get("complexity", "medium")
            complexities[complexity] = complexities.get(complexity, 0) + 1

            # Count sentiments
            sentiment = doc.metadata.get("sentiment", "neutral")
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

            # Count keywords
            keywords = doc.metadata.get("keywords", [])
            total_keywords += len(keywords)

        return {
            "total_documents": len(documents),
            "topics": topics,
            "complexity_distribution": complexities,
            "sentiment_distribution": sentiments,
            "total_keywords": total_keywords,
            "avg_keywords_per_doc": total_keywords / len(documents) if documents else 0,
        }

    @staticmethod
    def _parse_unstructured_response(response: str) -> Dict[str, Any]:
        """Parse unstructured LLM response"""
        # Simple parsing - in production, use more robust parsing
        return {
            "summary": response.split("\n")[0] if response else "",
            "keywords": [],
            "topic": "general",
            "complexity": "medium",
            "entities": [],
            "sentiment": "neutral",
        }

    @staticmethod
    def _get_default_metadata() -> Dict[str, Any]:
        """Get default metadata when extraction fails"""
        return {
            "summary": "Unable to extract summary",
            "keywords": [],
            "topic": "unknown",
            "complexity": "medium",
            "entities": [],
            "sentiment": "neutral",
        }
