# Phase 6: Frontend UI - Technical Design

**Change ID**: `phase-6-frontend-ui`
**Version**: 1.0

## Context

The RAG system backend (Phases 1-5) provides a REST API for document management and question-answering. This phase builds an interactive web interface for users to:
- Upload documents and manage collections
- Ask questions with configurable retrieval strategies
- View streamed responses with source citations
- Save and manage conversation history
- Use across devices (desktop, tablet, mobile)

## Goals

- Provide intuitive, fast user interface for RAG interaction
- Support modern web browsers (Chrome, Firefox, Safari, Edge)
- Accessible to users with disabilities (WCAG 2.1 Level AA)
- Mobile-first responsive design
- Real-time response streaming
- Persistent conversation history

## Non-Goals

- Authentication/authorization (Phase 7)
- Advanced analytics/tracking (Phase 8)
- Multi-user collaboration (Phase 9)
- Voice input/output (Future)
- Offline support (Future)
- Multi-language i18n (Future)

## Architectural Decisions

### 1. Framework: React 19 + TypeScript

**Decision**: Use React 19 with TypeScript for type safety and modern features.

**Alternatives Considered**:
- Vue 3: Smaller ecosystem, fewer templates/examples
- Angular: More opinionated, steeper learning curve
- Svelte: Emerging, less community support

**Rationale**:
- React 19 includes automatic component memoization and improved hooks
- TypeScript provides compile-time type checking
- Large ecosystem: Tailwind, React Router, SWR, etc.
- Fast development with Vite (instant HMR)
- Strong community support and documentation

**Trade-offs**:
- Larger bundle size than alternatives (~150KB gzipped React)
- Requires build step (Vite mitigates complexity)

---

### 2. Build Tool: Vite

**Decision**: Use Vite for development and production builds.

**Alternatives Considered**:
- Create React App (CRA): Slower dev server, slower builds
- Next.js: Overkill for SPA, adds complexity
- Webpack: Manual configuration required

**Rationale**:
- Instant module hot reload (HMR) for rapid development
- ~50x faster cold starts than CRA
- Optimized production builds (tree-shaking, code-splitting)
- Modern ESM-based dev server
- Requires minimal configuration

**Trade-offs**:
- Smaller community than CRA
- Different configuration than webpack-based tools

---

### 3. Styling: Tailwind CSS

**Decision**: Use Tailwind CSS utility-first framework for styling.

**Alternatives Considered**:
- CSS Modules: More CSS to write, no design system
- Styled Components: Runtime overhead, bundle size
- Material UI: Large component library, harder to customize
- Plain CSS: No design consistency, maintenance burden

**Rationale**:
- Utility-first speeds up development
- Built-in design system (colors, spacing, typography)
- Responsive design with breakpoint prefixes (`md:`, `lg:`)
- Dark mode support via class toggling
- Small footprint (treeshaking removes unused styles)
- Easy theming with CSS variables

**Trade-offs**:
- Learning curve for developers unfamiliar with utility CSS
- Verbose class names in JSX (mitigated by component patterns)

---

### 4. State Management: React Context + Hooks (No Redux)

**Decision**: Use React Context API + custom hooks for state management. No Redux.

**Alternatives Considered**:
- Redux: Industry standard, but adds complexity and boilerplate
- MobX: Simpler than Redux, but less mature
- Zustand: Lightweight alternative, good for simple state
- Recoil: Experimental, smaller ecosystem

**Rationale**:
- Context API built into React, no extra library
- Custom hooks (useChat, useDocuments) encapsulate domain logic
- Small app scope doesn't require Redux's devtools/time-travel
- Simpler testing: just test hooks, not Redux actions/reducers
- Easier for team onboarding

**Trade-offs**:
- No built-in devtools (can add React DevTools)
- Potential re-render overhead (mitigated with useMemo, useCallback)
- If app scales to 10+ pages, may reconsider

---

### 5. Data Fetching: Axios + Manual Caching

**Decision**: Use Axios for HTTP requests with manual retry logic. No SWR/React Query (yet).

**Alternatives Considered**:
- SWR: Automatic caching, revalidation, built-in hooks
- React Query: More features, larger bundle (~40KB)
- Fetch API: No interceptors, more manual work

**Rationale**:
- Axios provides request/response interceptors for global error handling
- Manual retry logic is straightforward for this app scope
- Simple error handling and timeouts
- Easy to test (mock axios)

**Trade-offs**:
- Manual cache invalidation (may add complexity later)
- Recommend migrating to SWR in Phase 8 as app grows

**Future Enhancement** (Phase 8):
- Add SWR for automatic caching and revalidation
- Reduces boilerplate in useChat, useDocuments hooks

---

### 6. API Streaming: Server-Sent Events (SSE)

**Decision**: Use Server-Sent Events (SSE) for real-time response streaming.

**Alternatives Considered**:
- WebSockets: Full-duplex, but overkill for one-way streaming
- Long polling: Less efficient, more server load
- Polling with delays: Slower user experience
- HTTP/2 Server Push: Browser support varies

**Rationale**:
- One-way streaming (server → client) matches our use case perfectly
- Simple to implement: standard HTTP connection, text events
- Built-in browser API (EventSource)
- Auto-reconnect with exponential backoff
- No special server library needed (FastAPI supports SSE)

**Trade-offs**:
- No re-connection on network failure (browser auto-reconnects)
- Limited to text data (works for our response chunks)

**Implementation**:
```typescript
// Backend (FastAPI)
@app.post("/question")
async def ask_question(...):
    async def event_generator():
        for chunk in response:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

// Frontend (React)
const response = await fetch(`/question`, {method: 'POST', body: ...});
const reader = response.body.getReader();
const decoder = new TextDecoder();
// Read streaming chunks...
```

---

### 7. Error Handling: Axios Interceptor + Retry

**Decision**: Use Axios interceptor to handle errors globally with exponential backoff retry.

**Rationale**:
- Single point for error handling (interceptor)
- Automatic retry for transient failures (5xx, 429, timeout)
- No retry for client errors (4xx)
- Exponential backoff: 1s, 2s, 4s (max 3 attempts)
- User feedback during retries

**Implementation**:
```typescript
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const retryCount = error.config.retryCount || 0;
    if (retryCount < 3 && isRetryableError(error)) {
      const delay = Math.pow(2, retryCount) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      error.config.retryCount = retryCount + 1;
      return apiClient(error.config);
    }
    throw error;
  }
);
```

---

### 8. Routing: React Router v7

**Decision**: Use React Router v7 for client-side routing (multi-page SPA).

**Alternatives Considered**:
- TanStack Router: Newer, type-safe, larger bundle
- No routing: Single-page SPA (simpler but limits navigation)

**Rationale**:
- Industry standard for React SPAs
- Clean URL structure (/chat, /documents, /settings)
- Lazy route code-splitting (load routes on demand)
- Simple setup with `<BrowserRouter>`, `<Routes>`, `<Route>`

**Routes**:
```
/ - Chat page (default)
/documents - Document management
/settings - Theme, session settings
/history - Conversation history (Phase 7)
```

---

### 9. Testing Strategy

**Decision**: Unit tests (Vitest) + integration tests (Playwright) + no snapshot tests.

**Rationale**:
- Vitest: Fast, runs in-process, great DX
- React Testing Library: Tests behavior, not implementation
- Playwright: Real browser E2E tests, multi-browser support
- No snapshot tests: Prone to false positives, hard to maintain

**Coverage Target**:
- Components: >80% coverage
- Hooks: >80% coverage
- Critical E2E flows: 5-10 tests (chat, upload, theme)

**Test File Locations**:
- Unit: `web/src/components/{ComponentName}.test.tsx`
- Hooks: `web/src/hooks/{hookName}.test.ts`
- E2E: `web/e2e/{test-name}.spec.ts`

---

### 10. Accessibility: WCAG 2.1 Level AA

**Decision**: Build accessible from the start, not as afterthought.

**Standards**:
- WCAG 2.1 Level AA (internationally recognized standard)
- Keyboard-only navigation (Tab, Enter, Escape, arrows)
- Screen reader support (semantic HTML + ARIA)
- Color contrast ≥4.5:1 (AA standard)
- Focus visible on all interactive elements

**Implementation**:
- Semantic HTML: `<button>`, `<nav>`, `<main>`, `<article>`
- ARIA labels: `aria-label`, `aria-describedby`, `aria-hidden`
- Keyboard handlers: `onKeyDown` for Enter, Escape, arrows
- Testing: Axe audits, manual screen reader testing (NVDA, VoiceOver)

---

### 11. Responsive Design: Mobile-First

**Decision**: Mobile-first approach with progressive enhancement for larger screens.

**Breakpoints** (Tailwind CSS):
- Mobile: 320px - 767px (default)
- Tablet: 768px - 1023px (`md:` prefix)
- Desktop: 1024px+ (`lg:` prefix)

**Layout Approach**:
- Mobile: Single column, full-width components
- Tablet: Two columns (chat 60%, sidebar 40%)
- Desktop: Three columns (sidebar 20%, chat 60%, panel 20%)

**Touch-Friendly**:
- Buttons: min 44x44px
- Spacing: 16px+ padding/margins on mobile
- No hover effects on touch (detect with @media (hover: none))

---

### 12. Dark Mode: CSS Variables + Context

**Decision**: Implement dark mode via CSS variables + React Context.

**Alternatives Considered**:
- Tailwind's `dark:` class: Simpler, but requires JavaScript to toggle
- CSS custom properties: Good for theming, needs context for state

**Implementation**:
```typescript
// ThemeContext
const ThemeContext = createContext<'light' | 'dark'>('light');

// CSS variables (in globals.css)
:root {
  --bg-primary: #ffffff;
  --text-primary: #000000;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1f2937;
    --text-primary: #ffffff;
  }
}

// Usage in components
<div className="bg-[var(--bg-primary)] text-[var(--text-primary)]">
```

**Persistence**:
- Save theme preference to localStorage
- On app load, read localStorage or use system preference
- Toggle button updates context + localStorage

---

### 13. Session Management: localStorage (Phase 6) → Backend (Phase 7)

**Decision**: Phase 6 uses localStorage for simple persistence. Upgrade to backend in Phase 7.

**Phase 6 Approach** (localStorage):
- Auto-save current session to localStorage on each message
- Load on app startup
- Simple, no server required
- Works offline

**Phase 7 Upgrade** (IndexedDB/API):
- Save sessions to backend API
- Support multiple saved sessions
- Cross-device access
- Collaborative sessions (future)

**Current Implementation**:
```typescript
// Auto-save on each message
useEffect(() => {
  localStorage.setItem('currentSession', JSON.stringify(messages));
}, [messages]);

// Load on mount
useEffect(() => {
  const saved = localStorage.getItem('currentSession');
  if (saved) setMessages(JSON.parse(saved));
}, []);
```

---

### 14. Build Optimization

**Decision**: Multi-stage Vite build with code-splitting and tree-shaking.

**Optimization Techniques**:
1. **Code Splitting**:
   - Route-based: Lazy load routes with React.lazy()
   - Component-based: Split large components (Document Upload)

2. **Tree-Shaking**:
   - Import only used functions: `import {debounce} from 'lodash-es'`
   - Avoid default exports in utility files

3. **Compression**:
   - Gzip in production (Vite applies automatically)
   - Target <500KB gzipped

4. **Caching**:
   - Vite generates chunked files with hash in name
   - Browser caches by hash

**Bundle Analysis**:
```bash
npm run build:analyze  # Generates visual bundle report
```

---

## Implementation Approach

### Phase 6A (MVP - 1 week)
1. Setup (Vite, Tailwind, TypeScript)
2. API client + error handling
3. Chat interface (input, display, streaming)
4. Basic document upload
5. Unit tests (>80%)

### Phase 6B (Complete - 1-2 weeks)
1. Query configuration (type selector, k slider)
2. Response display (sources, metadata)
3. Session management
4. Theme support
5. E2E tests + accessibility audit
6. Docker deployment

### Phase 6C (Polish - 1 week)
1. Performance optimization (Lighthouse >90)
2. Responsive design testing (3 breakpoints)
3. Mobile accessibility testing
4. Code review + documentation
5. Production deployment

---

## Risk Mitigation

### Risk 1: Real-time Streaming Complexity
**Risk**: SSE streaming might be unreliable or slow.
**Mitigation**:
- Test SSE implementation early (Task 5.5)
- Fallback to polling if SSE fails
- Set reasonable timeouts (30s per response)

### Risk 2: API Integration Issues
**Risk**: Frontend API calls fail due to backend changes.
**Mitigation**:
- Maintain API contract in openspec
- Test against real backend early and often
- Version API endpoints if breaking changes needed

### Risk 3: Performance Regression
**Risk**: Build size too large, slow initial load.
**Mitigation**:
- Monitor bundle size from start
- Code-split routes and large components
- Run Lighthouse audit regularly
- Target <500KB gzipped (strict)

### Risk 4: Accessibility Gaps
**Risk**: Built with good intentions but still not accessible.
**Mitigation**:
- Automated testing (Axe audits)
- Manual testing with real screen reader users
- Include accessibility in code reviews

### Risk 5: Mobile Responsiveness Issues
**Risk**: Works on desktop but breaks on mobile/tablet.
**Mitigation**:
- Mobile-first development (start with mobile layouts)
- Test on real devices early
- Use responsive testing tools (DevTools device mode)

---

## Future Enhancements (Phases 7-9)

### Phase 7: Authentication & Session Backend
- User login/registration
- Save sessions to backend (IndexedDB/API)
- Cross-device access
- Session sharing

### Phase 8: Advanced Features
- Conversation export (PDF/JSON)
- Analytics dashboard
- SWR for automatic caching
- Conversation branching (explore alternate answers)

### Phase 9: Collaboration & AI
- Multi-user conversations
- Real-time collaboration (WebSockets)
- Document annotation
- AI-powered suggestions

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Lighthouse Performance | >90 | Fast is fundamental |
| Lighthouse Accessibility | >95 | Inclusive design |
| Bundle Size | <500KB gzip | Fast initial load |
| Test Coverage | >80% | Confidence in changes |
| Mobile Load Time | <3s (4G) | Mobile users matter |
| E2E Test Pass Rate | 100% | Reliable features |
| Component Render Time | <100ms | Smooth interactions |

---

## References

- React 19 Docs: https://react.dev
- Vite Docs: https://vitejs.dev
- Tailwind CSS: https://tailwindcss.com
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- React Testing Library: https://testing-library.com/react
- Playwright: https://playwright.dev
