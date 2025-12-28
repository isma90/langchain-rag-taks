# Implementation Tasks: Configurable LLM Providers

## 1. Configuration Settings
- [x] 1.1 Add EMBEDDINGS_PROVIDER setting (openai|gemini)
- [x] 1.2 Add METADATA_PROVIDER setting (openai|gemini)
- [x] 1.3 Add QA_PROVIDER setting (openai|gemini)
- [x] 1.4 Implement provider validation with field_validator
- [x] 1.5 Support environment variable override

## 2. Embeddings Factory
- [x] 2.1 Create embeddings_factory.py module
- [x] 2.2 Implement create_embeddings_service() function
- [x] 2.3 Support OpenAI text-embedding-3-large
- [x] 2.4 Support Google Gemini embedding-001
- [x] 2.5 Return appropriate embeddings service

## 3. Metadata Handler Configuration
- [x] 3.1 Modify MetadataHandler __init__ to accept provider
- [x] 3.2 Create LLM instance based on METADATA_PROVIDER
- [x] 3.3 Support ChatOpenAI initialization
- [x] 3.4 Support ChatGoogleGenerativeAI initialization
- [x] 3.5 Preserve all existing metadata extraction behavior

## 4. Chain Builder Configuration
- [x] 4.1 Modify ChainBuilder to use configurable LLM
- [x] 4.2 Read QA_PROVIDER from settings
- [x] 4.3 Create appropriate LLM for prompts
- [x] 4.4 Preserve all prompt configurations

## 5. Qdrant Manager Updates
- [x] 5.1 Update QdrantVectorStoreManager to use factory
- [x] 5.2 Call create_embeddings_service()
- [x] 5.3 Pass embeddings to QdrantVectorStore
- [x] 5.4 Maintain backward compatibility

## 6. Testing & Verification
- [x] 6.1 Verify OpenAI configuration works
- [x] 6.2 Verify Gemini configuration works
- [x] 6.3 Verify hybrid configuration works
- [x] 6.4 Verify default (OpenAI) works when no env vars
- [x] 6.5 Verify cost savings with Gemini-only config

## 7. Documentation
- [x] 7.1 Document in openspec format (this file)
- [x] 7.2 Create spec deltas for llm-configuration capability
