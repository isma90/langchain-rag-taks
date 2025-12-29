# Implementation Tasks: Fix RAG Collection Scope

## 1. Type System Updates
- [ ] 1.1 Remove collectionName from Session interface
- [ ] 1.2 Update Session type definition in types/chat.ts
- [ ] 1.3 Verify no compilation errors

## 2. Application State Management
- [ ] 2.1 Define global collection constant in App.tsx
- [ ] 2.2 Remove collection reference from createNewSession()
- [ ] 2.3 Update all API calls to use global collection
- [ ] 2.4 Ensure collection is constant across all operations

## 3. API Integration
- [ ] 3.1 Update handleSendMessage to not pass collectionName
- [ ] 3.2 Verify api.askQuestion() uses global collection by default
- [ ] 3.3 Update document upload to use global collection name

## 4. Session Management
- [ ] 4.1 Verify sessions only store chat history
- [ ] 4.2 Verify no collection metadata in sessions
- [ ] 4.3 Ensure localStorage doesn't duplicate collection info

## 5. Frontend Rebuild & Testing
- [ ] 5.1 Rebuild frontend: npm run build
- [ ] 5.2 Rebuild Docker image: podman-compose build frontend
- [ ] 5.3 Restart frontend container
- [ ] 5.4 Verify no TypeScript errors

## 6. Functional Testing
- [ ] 6.1 Upload documents - should be global
- [ ] 6.2 Create session 1, ask question → uses global RAG
- [ ] 6.3 Create session 2, ask question → uses same RAG
- [ ] 6.4 Switch between sessions → same answers available
- [ ] 6.5 Verify chat history per-session but RAG is shared
