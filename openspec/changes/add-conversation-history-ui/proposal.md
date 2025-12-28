# Change: Add Conversation History UI

## Why

Users need to maintain conversation history across page reloads and easily switch between multiple separate conversations. Currently, all messages are lost on page refresh and there's no way to access previous chats.

## What Changes

- Implement conversation session management with persistent storage in localStorage
- Add ConversationSidebar component to display conversation history
- Auto-create new blank conversation on page reload
- Auto-scroll to bottom when new messages arrive
- Enable switching between conversations via sidebar

## Impact

- **Affected specs**: `frontend-ui`
- **Affected code**:
  - `web/src/App.tsx` - Complete refactor to session-based architecture
  - `web/src/components/ConversationSidebar.tsx` - New sidebar component (147 lines)
  - `web/src/types/chat.ts` - Session interface
  - `web/src/hooks/useLocalStorage.ts` - Existing localStorage hook
- **Breaking changes**: None - existing message interface preserved within sessions
- **User impact**: Improved UX with persistent chat history and better message navigation
