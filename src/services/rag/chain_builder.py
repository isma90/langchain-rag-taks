"""
RAG Chain Builder

Builds LangChain Expression Language (LCEL) chains for question-answering.
Supports multiple query types with specialized prompt templates.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from src.utils.logging_config import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class QueryType(Enum):
    """Supported query types for RAG"""
    GENERAL = "general"
    RESEARCH = "research"
    SPECIFIC = "specific"
    COMPLEX = "complex"


class RAGChainBuilder:
    """
    Builder for LCEL RAG chains with different prompt templates.

    Supports:
    - General Q&A (simple, direct answers)
    - Research (detailed, source-aware, comparative)
    - Specific (targeted to particular domains)
    - Complex (multi-step reasoning, synthesis)
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm: Optional[BaseLanguageModel] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize RAG chain builder.

        Args:
            retriever: LangChain retriever for document search
            llm: Language model (defaults to OpenAI GPT-4o)
            temperature: LLM temperature for response generation
        """
        self.retriever = retriever
        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            max_retries=3,  # Retry on rate limit (429) with exponential backoff
        )
        self.temperature = temperature
        logger.info(f"RAGChainBuilder initialized with {settings.openai_model}")

    def _format_docs(self, docs) -> str:
        """Format retrieved documents for context."""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            formatted.append(f"[Document {i} - {source}]\n{doc.page_content}")
        return "\n\n".join(formatted)

    def _get_general_prompt(self) -> ChatPromptTemplate:
        """Simple, direct Q&A prompt."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions based on the provided documents.

Provide clear, concise answers directly addressing the user's question.
If the answer isn't in the documents, say so clearly.
Keep responses focused and to the point."""),
            ("human", """Answer the following question based on these documents:

Documents:
{context}

Question: {question}

Answer:"""),
        ])

    def _get_research_prompt(self) -> ChatPromptTemplate:
        """Detailed research-focused prompt."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a research assistant providing detailed, well-sourced answers.

Guidelines:
- Provide comprehensive answers with multiple perspectives
- Always cite sources (document numbers)
- Include relevant details and nuances
- Highlight key concepts and relationships
- If there are different viewpoints, present them all
- Be thorough while remaining organized"""),
            ("human", """Provide a detailed research answer to the following question based on these documents:

Documents:
{context}

Question: {question}

Include:
1. Direct answer to the question
2. Supporting details from documents
3. Source citations
4. Related concepts

Answer:"""),
        ])

    def _get_specific_prompt(self) -> ChatPromptTemplate:
        """Domain-specific prompt for targeted questions."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a subject matter expert answering domain-specific questions.

Guidelines:
- Use technical terminology appropriately
- Focus on the most relevant information
- Provide practical, actionable insights
- Reference specific document sections
- Highlight any limitations or caveats"""),
            ("human", """Answer this specific domain question based on the documents:

Documents:
{context}

Question: {question}

Provide a focused, expert answer:"""),
        ])

    def _get_complex_prompt(self) -> ChatPromptTemplate:
        """Complex multi-step reasoning prompt."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an analytical assistant handling complex questions requiring synthesis and reasoning.

Guidelines:
- Break down complex questions into components
- Synthesize information from multiple documents
- Show your reasoning step-by-step
- Identify assumptions and limitations
- Provide balanced conclusions
- Use clear logical structure"""),
            ("human", """Analyze and answer this complex question using the provided documents:

Documents:
{context}

Question: {question}

Provide:
1. Question breakdown
2. Key findings from each relevant source
3. Synthesis and analysis
4. Conclusions
5. Any open questions or limitations

Answer:"""),
        ])

    def build_general_chain(self):
        """Build simple Q&A chain."""
        logger.info("Building GENERAL query chain")

        prompt = self._get_general_prompt()

        return (
            {
                "context": self.retriever | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
        )

    def build_research_chain(self):
        """Build research-focused chain."""
        logger.info("Building RESEARCH query chain")

        prompt = self._get_research_prompt()

        return (
            {
                "context": self.retriever | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
        )

    def build_specific_chain(self):
        """Build domain-specific chain."""
        logger.info("Building SPECIFIC query chain")

        prompt = self._get_specific_prompt()

        return (
            {
                "context": self.retriever | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
        )

    def build_complex_chain(self):
        """Build complex reasoning chain."""
        logger.info("Building COMPLEX query chain")

        prompt = self._get_complex_prompt()

        return (
            {
                "context": self.retriever | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
        )

    def build_chain(self, query_type: str = "general"):
        """
        Build appropriate chain for query type.

        Args:
            query_type: Type of query (general, research, specific, complex)

        Returns:
            Built LCEL chain

        Usage:
            chain = builder.build_chain(query_type="research")
            answer = chain.invoke("What is machine learning?")
        """
        query_type = query_type.lower()

        if query_type == "general":
            return self.build_general_chain()
        elif query_type == "research":
            return self.build_research_chain()
        elif query_type == "specific":
            return self.build_specific_chain()
        elif query_type == "complex":
            return self.build_complex_chain()
        else:
            logger.warning(f"Unknown query type '{query_type}', defaulting to general")
            return self.build_general_chain()
