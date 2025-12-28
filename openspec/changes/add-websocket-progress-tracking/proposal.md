# Change: Add WebSocket Progress Tracking

## Why

Users uploading large documents need real-time visibility into processing progress. Previous synchronous uploads would timeout and provide no feedback, creating poor UX and confusion about whether processing was happening.

## What Changes

- Implement `/upload` endpoint that returns immediately with `upload_id`
- Add background task processing for documents with progress updates
- Create `/ws/{upload_id}` WebSocket endpoint for real-time progress streaming
- Track 7 distinct processing states: received, extracting, chunking, enriching, indexing, completed, failed

## Impact

- **Affected specs**: `document-processing`, `api-endpoints`
- **Affected code**:
  - `src/services/processing/progress_tracker.py` - New progress tracking service
  - `src/api/main.py:226-323` - `/upload` endpoint and WebSocket handler
  - `src/services/rag/rag_service.py` - New progress-aware initialization method
  - `web/src/components/DocumentUpload.tsx` - WebSocket integration
- **Breaking changes**: None - `/initialize` endpoint remains unchanged
- **User impact**: Better feedback during document processing, no timeouts on large uploads
