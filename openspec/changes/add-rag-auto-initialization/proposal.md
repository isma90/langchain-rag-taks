# Change: Add RAG Auto-Initialization

## Why

Users need to ask questions immediately after uploading documents without requiring an explicit `/initialize` endpoint call. Currently, the `/question` endpoint fails with "Service not initialized" error if called before manual initialization, creating a confusing user experience.

## What Changes

- Make `/question` endpoint detect uninitialized service state
- Automatically load documents from Qdrant Cloud collection when uninitialized
- Retry the question after successful auto-initialization
- Improve error messages to guide users on explicit initialization if auto-init fails

## Impact

- **Affected specs**: `rag-pipeline`
- **Affected code**:
  - `src/api/main.py:400-447` - Enhanced error handling in `/question` endpoint
  - Qdrant Cloud documents are auto-loaded, no local file system required
- **Breaking changes**: None - explicit initialization still works as before
- **User impact**: Seamless workflow - upload → ask questions → get answers, all without manual API calls
