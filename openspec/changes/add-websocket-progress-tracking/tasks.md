# Implementation Tasks: WebSocket Progress Tracking

## 1. Progress Tracking Service
- [x] 1.1 Create ProgressTracker class with upload state management
- [x] 1.2 Implement async callback system for progress updates
- [x] 1.3 Add automatic cleanup after 5 minutes
- [x] 1.4 Track: status, current_chunk, total_chunks, progress_percent

## 2. API Upload Endpoint
- [x] 2.1 Create `/upload` endpoint that returns immediately
- [x] 2.2 Generate unique `upload_id` using UUID
- [x] 2.3 Return UploadStartResponse with upload_id
- [x] 2.4 Schedule background processing task

## 3. WebSocket Endpoint
- [x] 3.1 Implement `/ws/{upload_id}` WebSocket endpoint
- [x] 3.2 Register progress update callback
- [x] 3.3 Stream ProgressResponse updates to client
- [x] 3.4 Handle client disconnect gracefully
- [x] 3.5 Implement 5-minute idle timeout

## 4. Background Processing
- [x] 4.1 Create `_process_upload_background` task
- [x] 4.2 Call RAGService with progress tracking
- [x] 4.3 Update progress for each pipeline stage
- [x] 4.4 Send completion or error message at end

## 5. Frontend Integration
- [x] 5.1 Modify DocumentUpload to call `/upload` endpoint
- [x] 5.2 Connect to WebSocket with returned upload_id
- [x] 5.3 Display animated progress bar (0-100%)
- [x] 5.4 Show status emoji and message
- [x] 5.5 Update chunk counter display

## 6. Testing & Verification
- [x] 6.1 Verify endpoint returns immediately
- [x] 6.2 Verify WebSocket receives progress updates
- [x] 6.3 Verify no timeout on long processing
- [x] 6.4 Verify proper error handling and display
- [x] 6.5 Verify cleanup after completion

## 7. Documentation
- [x] 7.1 Document in openspec format (this file)
- [x] 7.2 Create spec deltas for document-processing capability
