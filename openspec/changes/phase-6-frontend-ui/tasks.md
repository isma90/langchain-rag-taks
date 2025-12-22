# Phase 6: Frontend UI - Implementation Tasks

**Change ID**: `phase-6-frontend-ui`
**Target Timeline**: December 23-31, 2025

## 1. Project Setup & Infrastructure

- [ ] 1.1 Create React 19 + Vite project: `npm create vite@latest web -- --template react-ts`
- [ ] 1.2 Install Tailwind CSS and configure: `npm install -D tailwindcss postcss autoprefixer`
- [ ] 1.3 Setup TypeScript configuration (strict mode)
- [ ] 1.4 Create directory structure (components, hooks, context, services, types)
- [ ] 1.5 Install testing dependencies (Vitest, React Testing Library)
- [ ] 1.6 Install E2E test framework (Playwright or Cypress)
- [ ] 1.7 Configure ESLint and Prettier for code consistency
- [ ] 1.8 Create `.env.example` with `VITE_API_URL` variable
- [ ] 1.9 Update root `docker-compose.yml` to include frontend service
- [ ] 1.10 Create `.dockerignore` and `Dockerfile` for frontend (Node Alpine)

## 2. Core API Integration

- [ ] 2.1 Create `web/src/types/api.ts` with all response types (RAGResponse, InitResponse, etc.)
- [ ] 2.2 Create `web/src/types/chat.ts` with domain types (Message, Session, Document, etc.)
- [ ] 2.3 Create `web/src/services/api.ts` with Axios client and all methods
- [ ] 2.4 Implement error interceptor with retry logic (3 attempts, exponential backoff)
- [ ] 2.5 Create `web/src/hooks/useFetch.ts` for generic data fetching
- [ ] 2.6 Create `web/src/hooks/useApiClient.ts` to access API instance
- [ ] 2.7 Test API client against running backend (manual or integration test)

## 3. Theme & Global State

- [ ] 3.1 Create `web/src/context/ThemeContext.tsx` with dark/light support
- [ ] 3.2 Implement `web/src/hooks/useTheme.ts` to access theme
- [ ] 3.3 Create `web/src/components/Theme/ThemeToggle.tsx` (sun/moon button)
- [ ] 3.4 Create `web/src/styles/globals.css` with Tailwind imports and theme colors
- [ ] 3.5 Setup localStorage persistence for theme preference
- [ ] 3.6 Implement system theme detection (prefers-color-scheme media query)
- [ ] 3.7 Test theme switching and persistence in browser

## 4. Layout Components

- [ ] 4.1 Create `web/src/components/Layout/Header.tsx` with logo, title, theme toggle
- [ ] 4.2 Create `web/src/components/Layout/Sidebar.tsx` with collection list and nav
- [ ] 4.3 Create `web/src/components/Layout/Layout.tsx` with responsive grid (mobile/tablet/desktop)
- [ ] 4.4 Create `web/src/components/ErrorBoundary.tsx` for error catching
- [ ] 4.5 Implement responsive breakpoints (320px, 768px, 1024px)
- [ ] 4.6 Add ARIA labels and semantic HTML to layout
- [ ] 4.7 Test layout on 3 screen sizes (mobile 375px, tablet 768px, desktop 1280px)

## 5. Chat Interface - Input & Display

- [ ] 5.1 Create `web/src/components/Chat/ChatInput.tsx` with textarea, query type selector, k slider
- [ ] 5.2 Create `web/src/components/Chat/ChatMessage.tsx` for user/assistant messages
- [ ] 5.3 Implement markdown rendering in ChatMessage (marked.js)
- [ ] 5.4 Implement code syntax highlighting (Prism.js)
- [ ] 5.5 Create `web/src/components/Chat/ResponseStreaming.tsx` for SSE streaming
- [ ] 5.6 Create `web/src/components/Chat/ChatContainer.tsx` combining all chat components
- [ ] 5.7 Implement auto-scroll to latest message in ChatContainer
- [ ] 5.8 Add empty state UI with example questions
- [ ] 5.9 Implement keyboard shortcuts (Ctrl+Enter to send, Escape to clear)
- [ ] 5.10 Test chat input, message display, and response streaming

## 6. Chat Hooks & State Management

- [ ] 6.1 Create `web/src/hooks/useChat.ts` with message management and API integration
- [ ] 6.2 Create `web/src/context/SessionContext.tsx` for conversation persistence
- [ ] 6.3 Create `web/src/hooks/useSession.ts` to access session context
- [ ] 6.4 Implement localStorage auto-save on each message
- [ ] 6.5 Implement session loading on app startup
- [ ] 6.6 Implement session creation with UUID
- [ ] 6.7 Test chat flow: send message → get response → update state

## 7. Query Configuration Components

- [ ] 7.1 Create `web/src/components/Query/QueryTypeSelector.tsx` with 4 query types
- [ ] 7.2 Add icons and descriptions for each query type
- [ ] 7.3 Create `web/src/components/Query/RetrievalParameters.tsx` with k slider and MMR toggle
- [ ] 7.4 Implement keyboard navigation for query type selector (arrow keys)
- [ ] 7.5 Add tooltips for parameter explanations
- [ ] 7.6 Integrate with ChatContainer to pass parameters to API
- [ ] 7.7 Test query type selection and parameter changes

## 8. Response Display & Sources

- [ ] 8.1 Create `web/src/components/Results/SourcesList.tsx` to display retrieved documents
- [ ] 8.2 Implement source grouping by relevance (high, medium, low)
- [ ] 8.3 Add relevance score visualization (percentage bar or badge)
- [ ] 8.4 Create `web/src/components/Results/ResponseMetadata.tsx` for performance metrics
- [ ] 8.5 Implement expandable details for response metrics
- [ ] 8.6 Add copy-to-clipboard for sources and responses
- [ ] 8.7 Test sources display and metrics rendering

## 9. Document Management

- [ ] 9.1 Create `web/src/components/Documents/DocumentUpload.tsx` with drag-and-drop
- [ ] 9.2 Implement file type validation (.pdf, .txt, .md, .docx)
- [ ] 9.3 Add progress bar per file during upload
- [ ] 9.4 Implement collection name input with validation
- [ ] 9.5 Add chunking strategy selector dropdown
- [ ] 9.6 Create `web/src/components/Documents/DocumentList.tsx` to list collections
- [ ] 9.7 Implement collection stats display (document count, vector count, size)
- [ ] 9.8 Add delete collection with confirmation dialog
- [ ] 9.9 Implement search/filter by collection name
- [ ] 9.10 Test document upload, list, and deletion flows

## 10. Hooks - Documents & Utilities

- [ ] 10.1 Create `web/src/hooks/useDocuments.ts` with upload/list/delete methods
- [ ] 10.2 Create `web/src/hooks/useLocalStorage.ts` for state persistence
- [ ] 10.3 Integrate useDocuments with DocumentUpload and DocumentList
- [ ] 10.4 Test document upload to backend and state updates

## 11. Accessibility & WCAG Compliance

- [ ] 11.1 Add ARIA labels to all buttons, inputs, and regions
- [ ] 11.2 Use semantic HTML: `<button>`, `<nav>`, `<main>`, `<article>`
- [ ] 11.3 Ensure all interactive elements are keyboard accessible (Tab, Enter, Escape)
- [ ] 11.4 Test focus visible (outline) on all elements
- [ ] 11.5 Verify color contrast ratios ≥4.5:1 (use Axe checker)
- [ ] 11.6 Test with screen reader (NVDA or VoiceOver)
- [ ] 11.7 Implement `prefers-reduced-motion` media query for animations
- [ ] 11.8 Run Axe accessibility audit in CI/CD

## 12. Unit Tests - Components

- [ ] 12.1 Create test files for all components (*.test.tsx)
- [ ] 12.2 Test ChatInput: render, type, submit
- [ ] 12.3 Test ChatMessage: render user/assistant messages, markdown rendering
- [ ] 12.4 Test QueryTypeSelector: click type, keyboard navigation
- [ ] 12.5 Test DocumentUpload: drag-drop, file validation, upload
- [ ] 12.6 Test ErrorBoundary: catch errors, display message, retry
- [ ] 12.7 Achieve >80% coverage on components
- [ ] 12.8 Run `npm test` - all tests passing

## 13. Unit Tests - Hooks

- [ ] 13.1 Create test file for useChat hook
- [ ] 13.2 Create test file for useDocuments hook
- [ ] 13.3 Create test file for useFetch hook
- [ ] 13.4 Create test file for useLocalStorage hook
- [ ] 13.5 Create test file for useTheme hook
- [ ] 13.6 Test data fetching, state updates, error handling
- [ ] 13.7 Mock API responses
- [ ] 13.8 Run all hook tests - passing

## 14. End-to-End Tests

- [ ] 14.1 Create E2E test file: `web/e2e/chat-flow.spec.ts`
  - Load app → see empty state
  - Enter question → send
  - See response with sources
  - Check response metadata
- [ ] 14.2 Create E2E test file: `web/e2e/document-upload.spec.ts`
  - Navigate to Documents
  - Drag file to upload zone
  - Enter collection name
  - Select chunking strategy
  - Click upload → monitor progress
  - See success message
- [ ] 14.3 Create E2E test file: `web/e2e/theme-toggle.spec.ts`
  - Click theme button
  - Verify theme changes
  - Reload page
  - Verify theme persisted
- [ ] 14.4 Run all E2E tests - passing
- [ ] 14.5 Test on real backend (not mocked)

## 15. Responsive Design & Mobile Testing

- [ ] 15.1 Test layout on mobile (375px, iPhone SE)
  - Single column layout
  - Stacked sections
  - Full-width input
- [ ] 15.2 Test layout on tablet (768px, iPad)
  - Two-column layout
  - Chat left 60%, sidebar right 40%
- [ ] 15.3 Test layout on desktop (1280px, desktop)
  - Three-column layout
  - Sidebar, chat, panel
- [ ] 15.4 Verify touch interactions on mobile (no hover effects)
- [ ] 15.5 Check button sizes: min 44x44px on mobile
- [ ] 15.6 Test lazy loading for document list (if >100 items)

## 16. Performance Optimization

- [ ] 16.1 Code split large components with React.lazy and Suspense
- [ ] 16.2 Memoize components with React.memo to prevent unnecessary re-renders
- [ ] 16.3 Use useMemo and useCallback for expensive operations
- [ ] 16.4 Optimize images with responsive sizes and lazy loading
- [ ] 16.5 Run Lighthouse audit
  - Performance: >90
  - Accessibility: >95
  - Best Practices: >90
  - SEO: >90
- [ ] 16.6 Check bundle size: target <500KB gzipped
- [ ] 16.7 Profile with React DevTools to find bottlenecks

## 17. Documentation & Setup

- [ ] 17.1 Create `web/README.md` with setup, build, dev instructions
- [ ] 17.2 Document environment variables in `.env.example`
- [ ] 17.3 Create COMPONENT_GUIDE.md with component usage examples
- [ ] 17.4 Document API client usage and error handling
- [ ] 17.5 Add JSDoc comments to hooks and utilities
- [ ] 17.6 Update root README.md with frontend section
- [ ] 17.7 Create DEPLOYMENT.md for frontend deployment

## 18. Docker & Deployment

- [ ] 18.1 Create `web/Dockerfile` (multi-stage: build → serve with Node)
- [ ] 18.2 Create `web/.dockerignore` (exclude node_modules, .git, etc.)
- [ ] 18.3 Update `docker-compose.yml`:
  - Add frontend service (port 3000)
  - Link to API service
  - Volume mount for code (dev mode)
- [ ] 18.4 Build Docker image: `docker build -t rag-frontend:latest web/`
- [ ] 18.5 Test compose: `docker-compose up` - all services running
- [ ] 18.6 Test frontend access at `http://localhost:3000`
- [ ] 18.7 Create Nginx reverse proxy config (future: serve frontend + API from single port)

## 19. Integration Testing

- [ ] 19.1 Start backend: `docker-compose up api qdrant redis` (or `uv run`)
- [ ] 19.2 Start frontend: `npm run dev`
- [ ] 19.3 Test full flow: upload document → ask question → see response
- [ ] 19.4 Test error scenarios: API down, network error, invalid input
- [ ] 19.5 Test concurrent requests: multiple questions in quick succession
- [ ] 19.6 Test session persistence: reload page, verify session loaded

## 20. Code Review & Quality

- [ ] 20.1 Run ESLint: `npm run lint` - no errors
- [ ] 20.2 Run Prettier: `npm run format` - code formatted
- [ ] 20.3 Run TypeScript: `npm run type-check` - no type errors
- [ ] 20.4 Run tests: `npm test` - all passing (>80% coverage)
- [ ] 20.5 Run build: `npm run build` - no warnings
- [ ] 20.6 Request code review from team
- [ ] 20.7 Address review comments

## 21. Final Checklist

- [ ] 21.1 All components implemented and tested
- [ ] 21.2 All unit tests passing (>80% coverage)
- [ ] 21.3 All E2E tests passing
- [ ] 21.4 Accessibility audit passing (Axe, manual screen reader test)
- [ ] 21.5 Responsive design verified (3 breakpoints)
- [ ] 21.6 Performance targets met (Lighthouse >90)
- [ ] 21.7 Docker build successful and running
- [ ] 21.8 Integration testing complete
- [ ] 21.9 Documentation complete and accurate
- [ ] 21.10 Ready for production deployment

---

## Milestone Summary

- **Milestone 1** (Setup & API): Tasks 1-2 (2 days)
- **Milestone 2** (Core UI): Tasks 3-5 (3 days)
- **Milestone 3** (Features): Tasks 6-10 (3 days)
- **Milestone 4** (Quality): Tasks 11-16 (2 days)
- **Milestone 5** (Deploy): Tasks 17-21 (1 day)

**Total**: ~11 days, target completion December 31, 2025

