# Change: Fix RAG Collection Scope (Global vs Per-Session)

## Why

The RAG collection was being stored per-session, making the knowledge base session-specific instead of globally shared. This means each user's session would only see documents uploaded within that session, and collaborative/shared knowledge access wasn't possible.

## What Changes

- Move RAG collection from session-level to application-level global state
- Remove `collectionName` from Session interface (conversations don't own the RAG)
- Use fixed global collection name 'rag_documents' for all sessions
- Ensure all users/sessions access the same indexed documents
- Maintain local session-specific chat history (separate concern)

## Impact

- **Affected specs**: `frontend-ui`, `conversation-management`
- **Affected code**:
  - `web/src/types/chat.ts` - Remove collectionName from Session interface
  - `web/src/App.tsx` - Use global collection instead of session collection
  - `web/src/services/api.ts` - Calls already support optional collectionName (default used)
- **Breaking changes**: None - API already supports optional collection_name parameter
- **User impact**: RAG now properly shared across all sessions, all users can access uploaded documents
