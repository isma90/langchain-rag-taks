# Frontend UI - Global RAG Collection Scope

## ADDED Requirements

### Requirement: Global Shared RAG Knowledge Base
The system SHALL maintain a single shared RAG collection accessible to all conversation sessions, with all users accessing the same indexed documents.

#### Scenario: All sessions access same documents
- **WHEN** multiple conversation sessions are active
- **THEN** all sessions query against the same global 'rag_documents' collection
- **AND** documents indexed in any session are available to all sessions
- **AND** no per-session document isolation

#### Scenario: Global collection independent of session lifecycle
- **WHEN** a conversation session is created or deleted
- **THEN** RAG collection remains intact and accessible
- **AND** deleting a session doesn't affect the knowledge base
- **AND** collection persists across all sessions

#### Scenario: Document uploads affect all sessions
- **WHEN** user uploads documents via DocumentUpload
- **THEN** documents are indexed to global 'rag_documents' collection
- **AND** documents immediately available to all sessions
- **AND** no per-session upload directories or collections

### Requirement: Session-Specific Chat History
Conversation sessions SHALL maintain independent chat history while sharing the global RAG collection.

#### Scenario: Session stores only chat history
- **WHEN** Session object is created
- **THEN** it stores:
  - Session ID (unique per conversation)
  - Chat messages (user questions and assistant answers)
  - Conversation title and timestamps
  - **NOT** collection metadata or RAG configuration
- **AND** collection name is never stored in Session

#### Scenario: Sessions don't reference collection
- **WHEN** Session is loaded from localStorage
- **THEN** no collectionName field exists
- **AND** no migration logic needed
- **AND** default global collection is always used

### Requirement: Unified Q&A Across Sessions
The Q&A functionality SHALL use the global collection regardless of which session is active.

#### Scenario: Answer question in any session
- **WHEN** user submits question in a conversation
- **THEN** question is answered against global RAG collection
- **AND** session ID doesn't affect document retrieval
- **AND** same question in different sessions returns same answers

#### Scenario: Search results are consistent
- **WHEN** searching documents from different sessions
- **THEN** search results are identical
- **AND** retrieval time and document ranking are consistent
- **AND** no per-session filtering or isolation

## MODIFIED Requirements

### Requirement: Conversation Session Management
Sessions SHALL store chat history and metadata without ownership of RAG collections.

#### Scenario: Session interface redesigned
- **WHEN** Session type is defined
- **THEN** it includes:
  - `id`: Unique session identifier
  - `title`: Human-readable title
  - `messages`: Array of Message objects
  - `createdAt`: Session creation timestamp
  - `updatedAt`: Last activity timestamp
  - **REMOVED**: `collectionName` field
  - **REMOVED**: Any RAG configuration
- **AND** all metadata is conversation-focused

#### Scenario: New session uses global collection
- **WHEN** createNewSession() is called
- **THEN** new session has no collection assignment
- **AND** session immediately accesses global RAG
- **AND** no initialization overhead per session

### Requirement: Question Answering
The `/question` endpoint SHALL use the global collection by default when no collection is specified.

#### Scenario: Frontend omits collection from requests
- **WHEN** frontend calls api.askQuestion()
- **THEN** collectionName parameter is not sent
- **AND** API uses default 'rag_documents' collection
- **AND** no per-session collection parameter

#### Scenario: API defaults to global collection
- **WHEN** `/question` endpoint receives request without collection_name
- **THEN** uses 'rag_documents' collection
- **AND** response includes documents from global collection
- **AND** sources reference global knowledge base

## REMOVED Requirements

### Requirement: Per-Session RAG Collections
**Reason**: RAG should be globally shared, not session-specific
**Migration**: All sessions now use single 'rag_documents' collection

### Requirement: Collection Metadata in Sessions
**Reason**: Collection scope is application-level, not session-level
**Migration**: Sessions store only chat history, not RAG configuration
