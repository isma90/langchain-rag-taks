# RAG Frontend - Interactive Chatbot UI

React 19 + TypeScript + Vite frontend for the Retrieval-Augmented Generation (RAG) system.

## Features

- ✅ **Chat Interface** - Real-time conversation with RAG backend
- ✅ **Query Configuration** - 4 query types (general, research, specific, complex)
- ✅ **Response Display** - Message history with metadata
- ✅ **Theme Support** - Dark/Light mode with persistence
- ✅ **Responsive Design** - Mobile-first, 3 breakpoints
- ✅ **Accessibility** - WCAG 2.1 Level AA compliance
- ✅ **Type Safety** - Full TypeScript support

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running at `http://localhost:8000`

### Installation

```bash
cd web
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

Create a `.env.local` file:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/          # React components
│   ├── ChatMessage.tsx
│   ├── ChatInput.tsx
│   └── ...
├── hooks/              # Custom React hooks
│   ├── useLocalStorage.ts
│   ├── useTheme.ts
│   ├── useFetch.ts
│   └── ...
├── services/           # API client
│   └── api.ts
├── types/              # TypeScript types
│   ├── api.ts
│   └── chat.ts
├── App.tsx             # Root component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## Available Scripts

- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Check TypeScript types
- `npm run lint` - Run ESLint
- `npm run format` - Format with Prettier
- `npm run test` - Run unit tests
- `npm test:coverage` - Test coverage report

## Technologies

- **React 19** - UI framework
- **TypeScript 5.5+** - Type safety
- **Vite 5** - Build tool
- **Tailwind CSS 3.4** - Styling
- **Axios 1.6** - HTTP client
- **UUID** - Session IDs
- **Marked** - Markdown parsing
- **PrismJS** - Code highlighting

## Testing

### Unit Tests

```bash
npm run test
```

### Test Coverage

```bash
npm run test:coverage
```

## Deployment

### Docker

```bash
docker build -t rag-frontend:latest .
docker run -p 3000:3000 rag-frontend:latest
```

### docker-compose

See root `docker-compose.yml` for full stack deployment.

### Environment Variables

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Performance

- **Bundle Size**: <500KB gzipped
- **Load Time**: <3s on 4G
- **Lighthouse Score**: >90

## Accessibility

- WCAG 2.1 Level AA compliant
- Keyboard navigation (Tab, Enter, Escape)
- ARIA labels and semantic HTML
- Screen reader support
- Color contrast ≥4.5:1

## API Integration

Frontend consumes the RAG backend API:

- `POST /health` - Health check
- `POST /initialize` - Initialize collection
- `POST /question` - Ask question
- `POST /search` - Search documents
- `GET /stats` - Get statistics
- `DELETE /collection/{name}` - Delete collection

See `src/services/api.ts` for full API client.

## Development

### Code Style

- ESLint for linting
- Prettier for formatting
- TypeScript strict mode
- Tailwind CSS for styling

### Component Patterns

- Functional components with hooks
- Props typing with TypeScript
- Conditional rendering with classNames
- useCallback for memoization

## Future Enhancements

- Session management (Phase 7)
- File upload for documents
- Response streaming (SSE)
- Advanced search filters
- User authentication
- Analytics dashboard

## License

MIT

## Support

For issues or questions, see the main project README or OpenSpec specifications in `openspec/changes/phase-6-frontend-ui/`.
