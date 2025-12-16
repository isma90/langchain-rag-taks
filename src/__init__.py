"""RAG Project - Production-Ready Retrieval-Augmented Generation System"""

from src.config import settings
from src.utils import get_logger

__version__ = "1.0.0"
__author__ = "RAG Team"

logger = get_logger(__name__)
logger.info(f"Initializing RAG Project v{__version__}")

__all__ = [
    'settings',
    'logger',
    '__version__',
]
