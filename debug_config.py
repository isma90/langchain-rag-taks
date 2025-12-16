"""Debug configuration loading"""
from src.config.settings import settings

print(f"QDRANT_URL: {settings.qdrant_url}")
print(f"QDRANT_API_KEY: {settings.qdrant_api_key[:20]}...")
print(f"OpenAI API Key: {settings.openai_api_key[:20]}...")
