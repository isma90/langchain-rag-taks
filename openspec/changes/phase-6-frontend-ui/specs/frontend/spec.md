# Phase 6: Frontend UI - Interactive RAG Chatbot - Specification

**Change ID**: `phase-6-frontend-ui`
**Version**: 1.0
**Status**: PROPOSED

## Chat Interface Capability

### ADDED Requirements

#### Requirement: Chat Message Display Component

Display a conversational message thread with user and assistant messages.

**Specification**:
- Component: `ChatMessage`
- Props:
  - `message: Message` - Message object
  - `isUser: boolean` - Sender type
  - `showSources?: boolean` - Display source documents
  - `onSourceClick?: (source: Document) => void` - Source click handler
- Features:
  - Markdown rendering for responses
  - Code syntax highlighting (Prism.js)
  - Timestamp and metadata
  - Copy message to clipboard
  - Source document links (if applicable)
- Styling: Tailwind CSS with theme support
- Accessibility: ARIA labels, keyboard navigation

**Scenarios**:
1. User message displays with right alignment, blue background
2. Assistant response displays with left alignment, gray background
3. Code blocks in response have syntax highlighting
4. Sources list appears below response with document preview
5. Clicking source opens document viewer modal

**File**: `web/src/components/ChatMessage.tsx`

---

#### Requirement: Chat Input Component

Text input for user questions with submit functionality.

**Specification**:
- Component: `ChatInput`
- Features:
  - Multi-line textarea (auto-grow)
  - Syntax for `@mentions` to reference documents
  - Query type selector inline: dropdown (general, research, specific, complex)
  - Retrieval parameter `k` slider (1-20, default 5)
  - Send button with loading state
  - Keyboard submit: Shift+Enter or Ctrl+Enter
- Validation:
  - Non-empty message required
  - Max 4000 characters
  - API call debouncing (500ms)
- Accessibility: Tab navigation, ARIA labels

**Scenarios**:
1. User types question → text appears in textarea
2. User selects query type from dropdown → type highlighted in input
3. User moves `k` slider → preview updates to show "Retrieve X documents"
4. User presses Ctrl+Enter → message sent, input cleared
5. Send button disabled while API call in progress (loading spinner)

**File**: `web/src/components/ChatInput.tsx`

---

#### Requirement: Chat Container Component

Main chat interface combining message display and input.

**Specification**:
- Component: `ChatContainer`
- Features:
  - Message list with auto-scroll to latest
  - Conversation context (current collection, session)
  - Loading skeleton during response streaming
  - Error state with retry button
  - Empty state with example questions
  - Conversation session info (title, created, updated)
- State:
  - `messages: Message[]` - Chat history
  - `loading: boolean` - API call in progress
  - `error: string | null` - Error message
  - `currentSession: Session` - Active conversation
- Hooks:
  - `useChat()` - Message management
  - `useDocuments()` - Collection context

**Scenarios**:
1. Page load → empty state with welcome message and example questions
2. User submits question → message added to list, input disabled
3. API responds → response streamed character-by-character (via SSE)
4. Response complete → sources displayed, input re-enabled
5. Error occurs → error message shown with retry button
6. User clicks example question → auto-filled in input

**File**: `web/src/components/ChatContainer.tsx`

---

## Document Management Capability

### ADDED Requirements

#### Requirement: Document Upload Component

Allow users to upload documents for RAG indexing.

**Specification**:
- Component: `DocumentUpload`
- Features:
  - Drag-and-drop area for files
  - File type filtering: `.pdf`, `.txt`, `.md`, `.docx` (via MIME types)
  - Multiple file selection
  - Progress bar per file
  - Success/error feedback per file
  - Collection name input (required)
  - Chunking strategy selector (recursive, semantic, markdown, HTML)
- API Integration:
  - POST `/initialize` with files
  - Streaming progress updates
  - Cancel button during upload
- Validation:
  - Max 5 files per upload
  - Max 50MB per file
  - Collection name 3-50 characters, alphanumeric + spaces/dashes

**Scenarios**:
1. User drags PDF file onto drop zone → file appears in preview
2. User selects chunking strategy → strategy icon highlights
3. User enters collection name "My Papers" → name validated
4. User clicks upload → progress bars show per file
5. Upload completes → success toast, file added to collection list

**File**: `web/src/components/DocumentUpload.tsx`

---

#### Requirement: Document List Component

Display uploaded documents and collections.

**Specification**:
- Component: `DocumentList`
- Features:
  - List all collections with metadata:
    - Collection name, created date, document count, vector count
    - Size estimate, last modified
  - Actions per collection:
    - View documents in collection
    - Delete collection (with confirmation)
    - Download collection metadata
  - Filter/search by name
  - Sort by: name, date, size
- API Integration:
  - GET `/stats` - Collection statistics
  - DELETE `/collection/{name}` - Delete collection
- Pagination: 10 items per page

**Scenarios**:
1. Page load → list of 3 collections shown with stats
2. User sorts by date descending → collections reordered
3. User filters by name "research" → only matching collections shown
4. User clicks delete on collection → confirmation dialog appears
5. User confirms delete → collection removed, list updated

**File**: `web/src/components/DocumentList.tsx`

---

## Query Configuration Capability

### ADDED Requirements

#### Requirement: Query Type Selector

Component to select RAG query type.

**Specification**:
- Component: `QueryTypeSelector`
- Query Types:
  1. **General**: Simple facts, straightforward answers (default)
  2. **Research**: Comparative analysis, multiple sources
  3. **Specific**: Domain-specific technical questions
  4. **Complex**: Multi-step reasoning, synthesis
- Features:
  - Radio button or card-based selection
  - Description text per type
  - Icon per type (magnifying glass, book, gear, lightbulb)
  - Keyboard navigation (arrows, Enter)
  - Visual feedback (selected state, hover)
- Default: `general`

**Scenarios**:
1. User clicks "Research" card → card highlights blue, description shows
2. User presses right arrow key → moves to next type
3. User selects "Complex" → returns `query_type: "complex"`
4. Type persists across messages in session

**File**: `web/src/components/QueryTypeSelector.tsx`

---

#### Requirement: Retrieval Parameters Panel

Configure document retrieval (k parameter).

**Specification**:
- Component: `RetrievalParameters`
- Parameters:
  - `k` (number of documents): Slider 1-20, default 5
  - `use_mmr` (boolean toggle): Use Maximum Marginal Relevance
  - `metadata_filter` (optional string): Filter by topic/complexity
- Features:
  - Slider with numeric input
  - Toggle switches with labels
  - Explanation tooltips (hover)
  - Reset to defaults button
  - Live preview: "Retrieve X diverse documents"
- Validation:
  - k must be 1-20 integer
  - Metadata filter max 100 characters

**Scenarios**:
1. User moves k slider to 10 → preview updates to "Retrieve 10 documents"
2. User enables MMR toggle → explanation tooltip shows
3. User enters metadata filter "complexity:complex" → filter applied
4. User clicks reset → k=5, MMR=false, filter=""

**File**: `web/src/components/RetrievalParameters.tsx`

---

## Response Display Capability

### ADDED Requirements

#### Requirement: Response Streaming Display

Show LLM response as it streams character-by-character.

**Specification**:
- Component: `ResponseStreaming`
- Features:
  - Server-Sent Events (SSE) connection to /question endpoint
  - Real-time character append to response text
  - Cursor animation while streaming
  - Estimated time remaining (based on characters/sec)
  - Stop/abort button
  - Copy response to clipboard
- API Integration:
  - POST /question with streaming enabled
  - Handle SSE events: `data: {answer_chunk}`
  - Handle `done` event when complete
- Performance:
  - Batch DOM updates (every 10 chars or 50ms)
  - Smooth scrolling to latest text

**Scenarios**:
1. API responds with SSE stream → text appears character by character
2. User reads response while it streams → no lag
3. Response nearly complete → "Estimated 2 seconds remaining" shows
4. User clicks stop → SSE connection closed, response truncated
5. Response completes → "Completed in 3.2s" shows

**File**: `web/src/components/ResponseStreaming.tsx`

---

#### Requirement: Sources Display Component

Show retrieved documents and metadata.

**Specification**:
- Component: `SourcesList`
- Features:
  - List of source documents used for response
  - Per source:
    - Document title and file name
    - Relevance score (0-1, as percentage)
    - Chunk preview (first 150 chars)
    - Metadata badges: topic, complexity, keywords
    - Click to expand full chunk
    - Copy chunk to clipboard
  - Total sources count at top
  - Grouped by relevance (high: >0.7, medium: 0.4-0.7, low: <0.4)
- Sort: By relevance score descending

**Scenarios**:
1. Response completes → sources list appears below
2. User sees 3 sources grouped by relevance
3. User clicks source title → full chunk expands in modal
4. User hovers on relevance score → tooltip shows calculation
5. User clicks copy icon → chunk copied to clipboard

**File**: `web/src/components/SourcesList.tsx`

---

#### Requirement: Response Metadata Display

Show performance metrics and statistics.

**Specification**:
- Component: `ResponseMetadata`
- Metrics:
  - Documents retrieved (count)
  - Retrieval time (ms)
  - Generation time (ms)
  - Total time (ms)
  - Model used (e.g., gpt-4o)
  - Query type used
  - Collection name
- Display:
  - Compact row below response
  - Expandable for full details
  - Icons per metric (clock, document, etc.)
  - Tooltips on hover
- Styling: Gray text, small font (12-14px)

**Scenarios**:
1. Response shows → metadata row appears: "3 docs | 245ms | gpt-4o"
2. User hovers on time → tooltip shows breakdown
3. User clicks expand → full metrics shown with explanations

**File**: `web/src/components/ResponseMetadata.tsx`

---

## Theme & Styling Capability

### ADDED Requirements

#### Requirement: Theme System (Dark/Light)

Support dark and light color schemes with persistence.

**Specification**:
- Context: `ThemeContext` - Global theme state
- Hook: `useTheme()` - Access/change theme
- Themes:
  - **Light**: White backgrounds, dark text (default)
  - **Dark**: Dark gray/black backgrounds, light text
- Persistence:
  - Save preference to localStorage
  - Read on app load
  - System preference detection (prefers-color-scheme media query)
- Colors (Tailwind palette):
  - Light: bg-white, text-gray-900, accent-blue-600
  - Dark: bg-gray-900, text-white, accent-blue-400
- Components:
  - Theme toggle button (sun/moon icon) in header

**Scenarios**:
1. First visit → system theme detected and applied
2. User clicks theme toggle → theme switches, saved to localStorage
3. User revisits → previously saved theme loaded
4. All components respond to theme context automatically

**File**: `web/src/context/ThemeContext.tsx`, `web/src/hooks/useTheme.ts`

---

#### Requirement: Responsive Design (Mobile-First)

Support mobile, tablet, and desktop layouts.

**Specification**:
- Breakpoints (Tailwind CSS):
  - Mobile (default): 320px - 767px
  - Tablet: 768px - 1023px
  - Desktop: 1024px+
- Layout Changes:
  - Mobile: Single column, full-width input
  - Tablet: Two columns (chat left 60%, sidebar right 40%)
  - Desktop: Three regions (sidebar left 20%, chat center 60%, panel right 20%)
- Touch-Friendly:
  - Button sizes: min 44x44px on mobile
  - Spacing increased on mobile
  - No hover effects on touch devices
- Performance:
  - Responsive images with srcset
  - Lazy loading for document list

**Scenarios**:
1. Mobile (375px): Single column layout, stacked sections
2. Tablet (768px): Chat and documents side-by-side
3. Desktop (1280px): Full three-column layout with sidebar

**File**: `web/src/components/Layout.tsx`, `web/tailwind.config.js`

---

## Accessibility Capability

### ADDED Requirements

#### Requirement: WCAG 2.1 Compliance

Support keyboard navigation and screen readers.

**Specification**:
- Standard: WCAG 2.1 Level AA
- Features:
  - All interactive elements keyboard accessible (Tab, Enter, Escape, arrows)
  - ARIA labels on buttons, inputs, regions
  - `aria-label`, `aria-describedby`, `aria-hidden` where needed
  - Semantic HTML: `<button>`, `<nav>`, `<main>`, `<article>`
  - Focus visible (outline) on all interactive elements
  - Color contrast ratio ≥ 4.5:1 for text
  - No content hidden from keyboard users
- Testing:
  - Axe accessibility testing in CI/CD
  - Manual screen reader testing (NVDA, VoiceOver)

**Scenarios**:
1. User tabs through page → all buttons focused in logical order
2. User presses Escape in modal → modal closes
3. User uses screen reader → all headings, regions announced
4. User has reduced motion → animations disabled per prefers-reduced-motion

**File**: `web/src/` - All components with ARIA attributes

---

## API Integration Capability

### ADDED Requirements

#### Requirement: Typed API Client

TypeScript client for backend REST API.

**Specification**:
- Module: `web/src/services/api.ts`
- Base URL: Configurable via `VITE_API_URL` env variable
- Axios HTTP client with interceptors
- Methods (types):
  - `askQuestion(question, queryType, k)` → `Promise<RAGResponse>`
  - `initializeCollection(name, documents[], strategy)` → `Promise<InitializeResponse>`
  - `searchDocuments(query, k)` → `Promise<SearchResponse>`
  - `getStats()` → `Promise<StatsResponse>`
  - `deleteCollection(name)` → `Promise<DeleteResponse>`
- Error Handling:
  - Axios error interceptor for global errors
  - Typed error responses with messages
  - Retry logic (3 attempts with exponential backoff)
- Types Defined:
  - `Message`, `RAGResponse`, `Document`, `Session`, etc.

**Scenarios**:
1. Chat input submit → `askQuestion()` called with message
2. Response received → `RAGResponse` parsed, sources extracted
3. Upload file → `initializeCollection()` sends files
4. API error (500) → error interceptor logs, UI shows message
5. Network timeout → retry after 1s, then 2s, then 4s

**File**: `web/src/services/api.ts`, `web/src/types/api.ts`

---

#### Requirement: Custom React Hooks

Encapsulate API and state management logic.

**Specification**:
- Hooks:
  - `useChat()` - Message history, send message, manage session
  - `useDocuments()` - Upload, list, delete collections
  - `useFetch<T>()` - Generic data fetching with loading/error states
  - `useLocalStorage<T>()` - Persist state to localStorage
  - `useApiClient()` - Access API client instance
- Each Hook:
  - Return: `{data, loading, error, methods}`
  - Handle errors gracefully
  - Cleanup on unmount
- Usage:
  - Reduce component complexity
  - Reusable across components
  - Testable in isolation

**Scenarios**:
1. Component mount → `useChat()` loads last 20 messages from API
2. New message sent → `useChat().sendMessage()` updates local state + API
3. Component unmount → cleanup functions run
4. Error occurs → `error` state set, component re-renders with error UI

**File**: `web/src/hooks/{useChat,useDocuments,useFetch,useLocalStorage}.ts`

---

## Session Management Capability

### ADDED Requirements

#### Requirement: Conversation Sessions

Save and load conversation history.

**Specification**:
- Session Object:
  - `id: string` - UUID
  - `title: string` - User-provided name
  - `collection: string` - Associated collection name
  - `messages: Message[]` - Chat history
  - `createdAt: ISO8601` - Creation timestamp
  - `updatedAt: ISO8601` - Last modification
  - `metadata: {queryType, avgResponseTime, etc.}`
- Storage:
  - localStorage: Current session (auto-saved on each message)
  - IndexedDB or API: Full session history (future Phase 7)
- Features:
  - Auto-save on each message
  - Manual save with custom title
  - Load previous session
  - List saved sessions
  - Export session as JSON/PDF
  - Delete session with confirmation

**Scenarios**:
1. User starts chat → new session created with UUID
2. User sends messages → session auto-saved to localStorage
3. User clicks "Save Session" → dialog prompts for title
4. User closes browser → session persists in localStorage
5. User revisits → previous session auto-loaded from localStorage

**File**: `web/src/hooks/useSession.ts`, `web/src/context/SessionContext.tsx`

---

## Error Handling & Retry Capability

### ADDED Requirements

#### Requirement: Error Boundary Component

Catch and display errors gracefully.

**Specification**:
- Component: `ErrorBoundary`
- Features:
  - Catch React component errors (render, lifecycle)
  - Display user-friendly error message
  - Show error details in development mode
  - Retry button to reset error state
  - Log errors to console/analytics
- Scope:
  - Wrap ChatContainer, DocumentList, main app
  - Don't catch event handler errors (use try/catch)
- UI:
  - Error icon, heading "Something went wrong"
  - Error message and error code
  - Retry button
  - Dark/light theme support

**Scenarios**:
1. Component throws error during render → ErrorBoundary catches
2. User sees error message with retry button
3. User clicks retry → component re-renders, error cleared
4. Multiple errors → each logged separately

**File**: `web/src/components/ErrorBoundary.tsx`

---

#### Requirement: API Retry with Exponential Backoff

Automatic retry for failed API requests.

**Specification**:
- Axios interceptor in API client
- Retry logic:
  - Max 3 attempts
  - Delays: 1s, 2s, 4s (exponential, 2^n)
  - Retry only on: 408, 429, 5xx status codes
  - Don't retry on: 400, 401, 403, 404
- User Feedback:
  - On first attempt: Show spinner
  - On retry: Update spinner with "Retrying..." text
  - After 3 failures: Show error message with manual retry button

**Scenarios**:
1. API returns 500 → auto-retry after 1s
2. Retry returns 500 → auto-retry after 2s
3. Final retry returns 200 → response processed
4. All retries fail → error message shown to user

**File**: `web/src/services/api.ts` (axios interceptor)

---

## Testing Capability

### ADDED Requirements

#### Requirement: Component Unit Tests

Test React components in isolation.

**Specification**:
- Framework: Vitest + React Testing Library
- Coverage Target: >80% of components
- Test Types:
  - Render tests: Component mounts without crashing
  - Interaction tests: Click buttons, type input, etc.
  - State tests: Props and hooks update correctly
  - Accessibility tests: ARIA labels, keyboard navigation
- Test File Location: `web/src/components/{ComponentName}.test.tsx`
- Mocking:
  - Mock API client (api.ts)
  - Mock React Router
  - Mock localStorage

**Scenarios**:
1. ChatInput renders → input element focused
2. User types question → text updates in real-time
3. User submits → onSubmit called with message
4. Component unmounts → cleanup runs

**File**: `web/src/components/{*.test.tsx}`

---

#### Requirement: End-to-End Tests

Test critical user journeys.

**Specification**:
- Framework: Playwright or Cypress
- Test Scope:
  1. Chat flow: Upload document → ask question → view response → check sources
  2. Session management: Save session → reload → verify session loaded
  3. Theme switching: Toggle theme → verify localStorage → reload
  4. Error handling: Simulate API error → verify retry → recovery
  5. Mobile responsiveness: Test on 3 breakpoints
- Coverage: Critical paths only (high value, quick to run)
- Location: `web/e2e/{test-name}.spec.ts`

**Scenarios**:
1. Test: "User can ask question and view sources"
   - Load app → see empty state
   - Enter question → send
   - See response with sources
   - Click source → modal opens

2. Test: "Upload document and initialize collection"
   - Navigate to Documents tab
   - Drag file to upload zone
   - Enter collection name
   - Click upload → monitor progress
   - See success message

**File**: `web/e2e/{*.spec.ts}`

---

## Architecture & Patterns

### Component Structure

```
web/src/
├── components/
│   ├── Chat/
│   │   ├── ChatContainer.tsx       # Main container
│   │   ├── ChatMessage.tsx         # Individual message
│   │   ├── ChatInput.tsx           # Input field
│   │   └── ResponseStreaming.tsx   # Streaming display
│   ├── Documents/
│   │   ├── DocumentUpload.tsx      # File upload
│   │   └── DocumentList.tsx        # List collections
│   ├── Query/
│   │   ├── QueryTypeSelector.tsx   # Query type picker
│   │   └── RetrievalParameters.tsx # k slider, MMR toggle
│   ├── Results/
│   │   ├── SourcesList.tsx         # Source documents
│   │   └── ResponseMetadata.tsx    # Performance metrics
│   ├── Layout/
│   │   ├── Header.tsx              # Navigation bar
│   │   ├── Sidebar.tsx             # Collection list
│   │   └── Layout.tsx              # Main grid layout
│   ├── Theme/
│   │   └── ThemeToggle.tsx         # Dark/light switch
│   └── ErrorBoundary.tsx           # Error handling
├── hooks/
│   ├── useChat.ts
│   ├── useDocuments.ts
│   ├── useFetch.ts
│   ├── useLocalStorage.ts
│   ├── useTheme.ts
│   └── useSession.ts
├── context/
│   ├── ThemeContext.tsx
│   └── SessionContext.tsx
├── services/
│   └── api.ts                      # API client
├── types/
│   ├── api.ts                      # API types
│   └── chat.ts                     # Domain types
├── styles/
│   └── globals.css                 # Tailwind imports
└── App.tsx                         # Root component
```

### State Management Pattern

- **Local State**: useState for component-level state (input value, toggle)
- **Context**: ThemeContext, SessionContext for global state
- **Hooks**: useChat, useDocuments for domain logic
- **API Client**: Cached responses with SWR or React Query (Phase 7)
- **Persistence**: localStorage for theme, current session

### Styling Pattern

- **Framework**: Tailwind CSS (utility-first)
- **Custom Theme**: CSS variables for colors in theme context
- **Responsive**: Mobile-first with `md:` and `lg:` prefixes
- **Dark Mode**: Tailwind's `dark:` prefix with custom color scheme

---

## Integration Points

**Phase 1** (Foundation):
- Uses configuration for API endpoint
- Theme preferences stored in localStorage

**Phase 5** (Deployment):
- Consumes REST API endpoints
- Served by Nginx as frontend service
- Environment variables for API URL

**Phase 4** (RAG Pipeline):
- Calls `/question` endpoint with streaming
- Displays RAGResponse with all fields

**Phase 3** (Vector Store):
- Lists collections from `/stats`
- Deletes collections via `/collection/{name}`

---

## Dependencies

```
react: ^19.2.3
react-dom: ^19.2.3
typescript: ^5.5.0
vite: ^5.0.0
tailwindcss: ^3.4.0
postcss: ^8.4.0
autoprefixer: ^10.4.0
react-router-dom: ^7.0.0
axios: ^1.6.0
classnames: ^2.3.0
prismjs: ^1.29.0  # Code highlighting
marked: ^11.0.0   # Markdown rendering
uuid: ^9.0.0      # Session IDs

# Dev dependencies
vitest: ^1.0.0
@testing-library/react: ^14.1.0
@testing-library/jest-dom: ^6.1.0
@testing-library/user-event: ^14.5.0
playwright: ^1.40.0  # Or cypress
@types/react: ^19.2.0
@types/node: ^20.0.0
eslint: ^8.55.0
prettier: ^3.1.0
```

---

## Success Metrics

- Component render time: <100ms (Lighthouse)
- API response time: <5s (end-to-end)
- Bundle size: <500KB gzipped
- Lighthouse score: >90 (performance, accessibility)
- Test coverage: >80% (components, hooks)
- Mobile load time: <3s (on 4G)

---

## Testing

- [ ] Component unit tests: ChatInput, ChatMessage, DocumentUpload
- [ ] Hook tests: useChat, useDocuments, useFetch
- [ ] E2E test: Ask question and view response
- [ ] E2E test: Upload document and initialize collection
- [ ] Accessibility audit (Axe)
- [ ] Responsive design testing (3 breakpoints)
- [ ] Performance profiling (Lighthouse)

---

## Status

- [ ] Design approved
- [ ] Implementation in progress
- [ ] Tests passing
- [ ] Code review approved
- [ ] Merged to main
- [ ] Deployed to production

**Target**: December 23-31, 2025

