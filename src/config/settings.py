"""
Production-Ready Configuration Management

Validates all settings from environment variables using Pydantic.
Ensures type safety and enforces production constraints.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv('.env')

logger = logging.getLogger(__name__)


class ProductionSettings(BaseSettings):
    """Production-ready configuration with validation"""

    # ========================================================================
    # OpenAI Configuration
    # ========================================================================
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-4o', env='OPENAI_MODEL')

    # ========================================================================
    # Google Gemini Configuration (for metadata extraction & embeddings)
    # ========================================================================
    gemini_api_key: str = Field(..., env='GEMINI_API_KEY')
    gemini_model: str = Field(default='gemini-2.5-flash', env='GEMINI_MODEL')

    # ========================================================================
    # Qdrant Cloud Configuration
    # ========================================================================
    qdrant_url: str = Field(default='https://localhost:6333', env='QDRANT_CLUSTER_ENDPOINT')
    qdrant_api_key: str = Field(default='default-key', env='QDRANT_API_KEY')
    qdrant_collection_name: str = Field(default='rag_documents', env='QDRANT_COLLECTION_NAME')

    # ========================================================================
    # Redis Configuration (Caching)
    # ========================================================================
    redis_url: str = Field(default='redis://localhost:6379', env='REDIS_URL')
    cache_ttl: int = Field(default=3600, env='CACHE_TTL')  # 1 hour

    # ========================================================================
    # LangSmith Configuration (Observability)
    # ========================================================================
    langsmith_api_key: Optional[str] = Field(None, env='LANGSMITH_API_KEY')
    langsmith_project: str = Field(default='rag-project', env='LANGSMITH_PROJECT')

    # ========================================================================
    # RAG Configuration
    # ========================================================================
    chunk_size: int = Field(default=1000, env='RAG_CHUNK_SIZE')  # tokens
    chunk_overlap: int = Field(default=200, env='RAG_CHUNK_OVERLAP')  # tokens
    retriever_k: int = Field(default=5, env='RAG_RETRIEVER_K')  # top-k results
    chunking_strategy: str = Field(default='recursive', env='CHUNKING_STRATEGY')  # recursive, semantic, markdown

    # ========================================================================
    # Embedding Configuration
    # ========================================================================
    embedding_model: str = Field(default='text-embedding-3-large', env='EMBEDDING_MODEL')
    embedding_dimensions: int = Field(default=512, env='EMBEDDING_DIMENSIONS')

    # ========================================================================
    # Server Configuration
    # ========================================================================
    langserve_port: int = Field(default=8000, env='LANGSERVE_PORT')
    langserve_host: str = Field(default='0.0.0.0', env='LANGSERVE_HOST')
    langserve_reload: bool = Field(default=False, env='LANGSERVE_RELOAD')

    # ========================================================================
    # Logging & Monitoring
    # ========================================================================
    log_level: str = Field(default='INFO', env='LOG_LEVEL')
    log_format: str = Field(default='json', env='LOG_FORMAT')  # json or text

    # ========================================================================
    # Rate Limiting
    # ========================================================================
    rate_limit_rpm: int = Field(default=10, env='RATE_LIMIT_RPM')  # requests per minute
    tokens_per_minute: int = Field(default=90000, env='TOKENS_PER_MINUTE')  # OpenAI limit

    # ========================================================================
    # Resilience & Performance
    # ========================================================================
    circuit_breaker_threshold: int = Field(default=5, env='CIRCUIT_BREAKER_THRESHOLD')
    circuit_breaker_timeout: int = Field(default=60, env='CIRCUIT_BREAKER_TIMEOUT')  # seconds
    retry_max_attempts: int = Field(default=3, env='RETRY_MAX_ATTEMPTS')

    # ========================================================================
    # Environment
    # ========================================================================
    environment: str = Field(default='development', env='ENVIRONMENT')  # development, staging, production
    debug: bool = Field(default=False, env='DEBUG')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is reasonable (tokens, not characters)"""
        if v < 100 or v > 5000:
            raise ValueError('chunk_size must be between 100 and 5000 tokens')
        return v

    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """Validate chunk overlap is reasonable"""
        if v < 0 or v > 500:
            raise ValueError('chunk_overlap must be between 0 and 500 tokens')
        return v

    @field_validator('qdrant_url')
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        """Validate Qdrant URL uses HTTPS in production"""
        # Allow localhost for development, HTTPS for Cloud
        if v and v != 'https://localhost:6333':
            if not (v.startswith('https://') or v.startswith('http://localhost')):
                raise ValueError('QDRANT_URL must use https:// for security (http://localhost allowed for dev)')
        return v

    @field_validator('embedding_dimensions')
    @classmethod
    def validate_embedding_dimensions(cls, v: int) -> int:
        """Validate embedding dimensions (text-embedding-3 supports 256-3072)"""
        if v not in [256, 512, 1536, 3072]:
            raise ValueError('embedding_dimensions must be one of: 256, 512, 1536, 3072')
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of: {", ".join(valid_levels)}')
        return v.upper()

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment"""
        valid_envs = ['development', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'environment must be one of: {", ".join(valid_envs)}')
        return v

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == 'production'

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == 'development'

    @property
    def chunk_size_tokens(self) -> int:
        """Alias for chunk_size (in tokens)"""
        return self.chunk_size

    @property
    def chunk_overlap_tokens(self) -> int:
        """Alias for chunk_overlap (in tokens)"""
        return self.chunk_overlap

    def __init__(self, **data):
        """Initialize settings and log configuration"""
        super().__init__(**data)

        # Override with environment variables if they exist
        if os.getenv('QDRANT_CLUSTER_ENDPOINT'):
            self.qdrant_url = os.getenv('QDRANT_CLUSTER_ENDPOINT')

        logger.info(f"Loaded configuration for environment: {self.environment}")
        if self.is_production:
            logger.warning("Running in PRODUCTION mode. Ensure all security measures are in place.")


# Singleton instance
try:
    settings = ProductionSettings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise
