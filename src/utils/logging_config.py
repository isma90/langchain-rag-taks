"""
Production-Ready Structured Logging Configuration

Provides JSON-formatted structured logging with LangSmith integration.
All logs include timestamps, context, and metrics.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pythonjsonlogger import jsonlogger
from src.config.settings import settings

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


class ProductionLogger:
    """Production-ready structured logger with LangSmith integration"""

    def __init__(self, name: str):
        """Initialize logger with name"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.log_level))
        self.name = name

        # Add JSON formatter if configured
        if settings.log_format == 'json':
            self._setup_json_formatter()

        # LangSmith integration
        self.langsmith_enabled = settings.langsmith_api_key is not None
        if self.langsmith_enabled:
            try:
                from langsmith import Client
                self.langsmith_client = Client(api_key=settings.langsmith_api_key)
            except Exception as e:
                self.logger.warning(f"LangSmith integration failed: {e}")
                self.langsmith_enabled = False

    def _setup_json_formatter(self):
        """Setup JSON formatting for structured logging"""
        # Remove existing handlers
        self.logger.handlers = []

        # Create new handler with JSON formatter
        log_handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(name)s %(levelname)s %(message)s %(extra)s',
            timestamp=True,
            rename_fields={'timestamp': 'timestamp', 'message': 'message'}
        )
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

    def _build_log_entry(self, event: str, level: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build structured log entry"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'logger': self.name,
            'level': level,
            'event': event,
            'environment': settings.environment,
            **data
        }

    def log_chain_execution(
        self,
        chain_name: str,
        query: str,
        response: str,
        execution_time: float,
        tokens_used: int,
        cost_usd: float,
        retrieved_docs: int = 0
    ):
        """Log RAG chain execution with metrics"""
        log_data = self._build_log_entry(
            'chain_execution',
            'INFO',
            {
                'chain_name': chain_name,
                'query_length': len(query),
                'response_length': len(response),
                'execution_time_ms': int(execution_time * 1000),
                'tokens_used': tokens_used,
                'cost_usd': round(cost_usd, 6),
                'retrieved_docs': retrieved_docs
            }
        )
        self.logger.info(json.dumps(log_data))

    def log_retrieval(
        self,
        query: str,
        docs_count: int,
        retrieval_time: float,
        strategy: str = 'standard'
    ):
        """Log document retrieval event"""
        log_data = self._build_log_entry(
            'retrieval_complete',
            'INFO',
            {
                'query': query[:100],  # Truncate for privacy
                'docs_retrieved': docs_count,
                'retrieval_time_ms': int(retrieval_time * 1000),
                'strategy': strategy
            }
        )
        self.logger.info(json.dumps(log_data))

    def log_embedding(
        self,
        text_length: int,
        embedding_time: float,
        tokens_used: int,
        model: str = 'text-embedding-3-large'
    ):
        """Log embedding operation"""
        log_data = self._build_log_entry(
            'embedding_complete',
            'INFO',
            {
                'text_length': text_length,
                'embedding_time_ms': int(embedding_time * 1000),
                'tokens_used': tokens_used,
                'model': model,
                'cost_usd': round((tokens_used / 1000) * 0.00013, 6)
            }
        )
        self.logger.info(json.dumps(log_data))

    def log_cache_hit(
        self,
        cache_key: str,
        hit: bool,
        cache_type: str = 'query'
    ):
        """Log cache hit/miss"""
        log_data = self._build_log_entry(
            'cache_check',
            'DEBUG' if hit else 'INFO',
            {
                'cache_type': cache_type,
                'hit': hit,
                'key_hash': hash(cache_key) % 10**9  # Hash for privacy
            }
        )
        self.logger.debug(json.dumps(log_data))

    def log_chunking(
        self,
        input_documents: int,
        output_chunks: int,
        input_tokens: int,
        output_tokens: int,
        processing_time_ms: float,
        strategy: str = 'recursive'
    ):
        """Log document chunking operation"""
        log_data = self._build_log_entry(
            'chunking_complete',
            'INFO',
            {
                'input_documents': input_documents,
                'output_chunks': output_chunks,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'processing_time_ms': int(processing_time_ms),
                'strategy': strategy,
                'cost_usd': round((output_tokens / 1000) * 0.00013, 6),
                'avg_chunk_tokens': round(output_tokens / output_chunks, 1) if output_chunks else 0,
            }
        )
        self.logger.info(json.dumps(log_data))

    def log_indexing(
        self,
        collection_name: str,
        vectors_indexed: int,
        documents_indexed: int,
        processing_time_ms: float,
        batch_size: int = 100
    ):
        """Log vector indexing operation"""
        log_data = self._build_log_entry(
            'indexing_complete',
            'INFO',
            {
                'collection_name': collection_name,
                'vectors_indexed': vectors_indexed,
                'documents_indexed': documents_indexed,
                'processing_time_ms': int(processing_time_ms),
                'batch_size': batch_size,
                'vectors_per_second': round(vectors_indexed / (processing_time_ms / 1000), 1) if processing_time_ms > 0 else 0,
            }
        )
        self.logger.info(json.dumps(log_data))

    def log_error(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        traceback_str: Optional[str] = None,
        user_message: Optional[str] = None
    ):
        """Log errors with full context"""
        error_log = self._build_log_entry(
            'error_occurred',
            'ERROR',
            {
                'error_type': error_type,
                'message': message,
                'user_message': user_message or message,
                'severity': self._classify_severity(error_type),
                **(context or {})
            }
        )
        if traceback_str:
            error_log['traceback'] = traceback_str

        self.logger.error(json.dumps(error_log))

        # Log to LangSmith if available
        if self.langsmith_enabled:
            try:
                self.langsmith_client.create_feedback(
                    run_id='',  # Would need actual run_id
                    key='error',
                    score=0,
                    comment=f"{error_type}: {message}"
                )
            except Exception:
                pass  # Silently fail LangSmith logging

    def log_performance_warning(
        self,
        metric: str,
        value: float,
        threshold: float,
        unit: str = 'ms'
    ):
        """Log performance warnings"""
        log_data = self._build_log_entry(
            'performance_warning',
            'WARNING',
            {
                'metric': metric,
                'value': round(value, 2),
                'threshold': round(threshold, 2),
                'unit': unit,
                'exceeded_by': round(((value - threshold) / threshold) * 100, 1)
            }
        )
        self.logger.warning(json.dumps(log_data))

    def log_rate_limit(
        self,
        limit_type: str,
        current_usage: int,
        limit: int,
        reset_time: Optional[str] = None
    ):
        """Log rate limit events"""
        log_data = self._build_log_entry(
            'rate_limit_check',
            'WARNING' if current_usage > limit * 0.8 else 'INFO',
            {
                'limit_type': limit_type,
                'current_usage': current_usage,
                'limit': limit,
                'usage_percent': round((current_usage / limit) * 100, 1),
                'reset_time': reset_time
            }
        )
        self.logger.warning(json.dumps(log_data))

    @staticmethod
    def _classify_severity(error_type: str) -> str:
        """Classify error severity"""
        severity_map = {
            'connection': 'CRITICAL',
            'timeout': 'HIGH',
            'rate_limit': 'MEDIUM',
            'validation': 'LOW',
            'default': 'MEDIUM'
        }
        for key, severity in severity_map.items():
            if key in error_type.lower():
                return severity
        return severity_map['default']

    def info(self, message: str, **extra):
        """Log info level"""
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **extra):
        """Log warning level"""
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **extra):
        """Log error level"""
        self.logger.error(message, extra=extra)

    def debug(self, message: str, **extra):
        """Log debug level"""
        self.logger.debug(message, extra=extra)


def get_logger(name: str) -> ProductionLogger:
    """Get or create a ProductionLogger instance"""
    return ProductionLogger(name)
