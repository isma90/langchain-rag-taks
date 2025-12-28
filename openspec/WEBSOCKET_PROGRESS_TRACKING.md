# WebSocket Real-Time Progress Tracking

## Overview

Implementation of real-time progress tracking for document uploads using WebSocket connections. Clients receive updates on document processing progress without timeout concerns.

## Problem Solved

- **Timeout Issues**: Previous synchronous uploads would timeout for large documents
- **No Feedback**: Users had no visibility into processing progress
- **UX Gap**: No way to show animated progress to users

## Solution Architecture

### Backend Components

**ProgressTracker Service** (`src/services/processing/progress_tracker.py`)
- Maintains upload state per `upload_id`
- Async callbacks for progress updates
- Tracks: status, current chunk, total chunks, progress percentage
- Automatic cleanup after 5 minutes

### API Endpoints

**POST /upload**
```json
Request:
{
  "collection_name": "rag_documents",
  "documents": [...],
  "force_recreate": false
}

Response (Immediate):
{
  "upload_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "received",
  "message": "Upload received. Total documents: 1",
  "timestamp": 1234567890
}
```

**WebSocket /ws/{upload_id}**

Streaming progress updates:
```json
{
  "upload_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "chunking",
  "progress_percent": 25.0,
  "current_chunk": 5,
  "total_chunks": 20,
  "message": "Chunking documents...",
  "timestamp": "2025-12-28T04:26:10.123456+00:00"
}
```

### Frontend Components

**DocumentUpload Component Updates**
- Calls `/upload` endpoint (returns immediately)
- Connects to WebSocket with returned `upload_id`
- Displays animated progress bar
- Shows status with emojis: 📥 📖 ✂️ ✨ 🗂️
- Updates chunk counter: "4 of 10"

## Processing States

1. **received** (📥): Upload received, queued for processing
2. **extracting** (🔍): Extracting text from documents
3. **chunking** (✂️): Splitting into chunks
4. **enriching** (✨): Extracting metadata
5. **indexing** (🗂️): Indexing in vector database
6. **completed** (✅): Successfully processed
7. **failed** (❌): Processing error

## Key Features

✅ **Immediate Response**: API returns upload_id within milliseconds
✅ **No Timeout**: Frontend waits indefinitely with WebSocket
✅ **Real-time Feedback**: Progress updates streamed live
✅ **Granular Tracking**: Per-chunk progress updates
✅ **Error Handling**: Displays error messages on failure
✅ **Auto-cleanup**: WebSocket closes automatically

## Implementation Details

### How It Works

1. User uploads document → API returns `upload_id` immediately
2. Frontend connects to `ws://api/ws/{upload_id}`
3. Backend processes in background task
4. Each chunk completion triggers progress update via WebSocket
5. Frontend updates progress bar (0% → 100%)
6. When complete, backend sends completion message
7. WebSocket closes, showing success message

### Timeout Configuration

- **HTTP Client**: 5 minutes (300 seconds)
- **WebSocket**: 5 minutes idle timeout
- **Backend Processing**: No timeout limit

## Usage Example

```typescript
// Frontend
const uploadResponse = await api.startUpload({
  collection_name: "rag_documents",
  documents: [...],
  force_recreate: false
})

const ws = new WebSocket(`ws://api/ws/${uploadResponse.upload_id}`)

ws.onmessage = (event) => {
  const progress = JSON.parse(event.data)
  console.log(`Progress: ${progress.progress_percent}%`)

  if (progress.status === 'completed') {
    ws.close()
    showSuccess()
  }
}
```

## Files Modified

- `src/services/processing/progress_tracker.py` - Progress tracking service
- `src/services/processing/__init__.py` - Module exports
- `src/api/main.py` - New endpoints and WebSocket handler
- `src/services/rag/rag_service.py` - Progress-aware processing method
- `web/src/components/DocumentUpload.tsx` - WebSocket integration
- `web/src/services/api.ts` - Upload API method

## Status

✅ **Implemented**: Fully functional with real-time progress updates
✅ **Tested**: WebSocket connections working correctly
✅ **Stable**: Auto-cleanup and error handling in place

## Future Enhancements

- Persist upload history in database
- Resume interrupted uploads
- Batch upload monitoring dashboard
- S3 pre-signed URLs for larger files
