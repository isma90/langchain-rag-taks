"""
Progress Tracker for Document Processing

Tracks document processing progress and broadcasts updates to WebSocket clients.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Processing status states"""
    RECEIVED = "received"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    ENRICHING = "enriching"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Progress update message"""
    upload_id: str
    status: ProcessingStatus
    progress_percent: float  # 0-100
    current_chunk: int
    total_chunks: int
    message: str
    timestamp: datetime

    def to_dict(self):
        return {
            "upload_id": self.upload_id,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class ProgressTracker:
    """
    Tracks document processing progress.

    Maintains state per upload_id and allows progress callbacks.
    """

    def __init__(self):
        """Initialize progress tracker"""
        self.uploads: Dict[str, Dict] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.lock = asyncio.Lock()

    async def start_upload(self, upload_id: str, total_chunks: int) -> None:
        """
        Start tracking a new upload.

        Args:
            upload_id: Unique upload identifier
            total_chunks: Total number of chunks to process
        """
        async with self.lock:
            self.uploads[upload_id] = {
                "status": ProcessingStatus.RECEIVED,
                "total_chunks": total_chunks,
                "current_chunk": 0,
                "started_at": datetime.utcnow(),
                "error": None,
            }
            self.callbacks[upload_id] = []

        logger.info(f"Started tracking upload {upload_id} with {total_chunks} chunks")

    async def update_progress(
        self,
        upload_id: str,
        status: ProcessingStatus,
        current_chunk: int,
        message: str = "",
    ) -> None:
        """
        Update processing progress.

        Args:
            upload_id: Upload identifier
            status: Current processing status
            current_chunk: Number of chunks processed
            message: Optional status message
        """
        if upload_id not in self.uploads:
            logger.warning(f"Upload {upload_id} not found")
            return

        async with self.lock:
            upload = self.uploads[upload_id]
            total_chunks = upload["total_chunks"]

            # Calculate progress percentage
            progress_percent = (
                (current_chunk / total_chunks * 100) if total_chunks > 0 else 0
            )

            # Create update
            update = ProgressUpdate(
                upload_id=upload_id,
                status=status,
                progress_percent=progress_percent,
                current_chunk=current_chunk,
                total_chunks=total_chunks,
                message=message or f"Processing chunk {current_chunk}/{total_chunks}",
                timestamp=datetime.utcnow(),
            )

            # Update state
            upload["status"] = status
            upload["current_chunk"] = current_chunk

            logger.debug(
                f"Upload {upload_id}: {status.value} - "
                f"{current_chunk}/{total_chunks} ({progress_percent:.1f}%)"
            )

            # Notify all callbacks
            await self._notify_callbacks(upload_id, update)

    async def complete_upload(self, upload_id: str) -> None:
        """
        Mark upload as completed.

        Args:
            upload_id: Upload identifier
        """
        if upload_id not in self.uploads:
            return

        async with self.lock:
            upload = self.uploads[upload_id]
            total_chunks = upload["total_chunks"]

            update = ProgressUpdate(
                upload_id=upload_id,
                status=ProcessingStatus.COMPLETED,
                progress_percent=100.0,
                current_chunk=total_chunks,
                total_chunks=total_chunks,
                message="Processing completed successfully",
                timestamp=datetime.utcnow(),
            )

            upload["status"] = ProcessingStatus.COMPLETED

            logger.info(f"Upload {upload_id} completed")

            # Notify callbacks
            await self._notify_callbacks(upload_id, update)

            # Cleanup
            await self._cleanup_upload(upload_id)

    async def fail_upload(self, upload_id: str, error: str) -> None:
        """
        Mark upload as failed.

        Args:
            upload_id: Upload identifier
            error: Error message
        """
        if upload_id not in self.uploads:
            return

        async with self.lock:
            upload = self.uploads[upload_id]

            update = ProgressUpdate(
                upload_id=upload_id,
                status=ProcessingStatus.FAILED,
                progress_percent=0.0,
                current_chunk=0,
                total_chunks=upload["total_chunks"],
                message=f"Processing failed: {error}",
                timestamp=datetime.utcnow(),
            )

            upload["status"] = ProcessingStatus.FAILED
            upload["error"] = error

            logger.error(f"Upload {upload_id} failed: {error}")

            # Notify callbacks
            await self._notify_callbacks(upload_id, update)

            # Cleanup
            await self._cleanup_upload(upload_id)

    def register_callback(self, upload_id: str, callback: Callable) -> None:
        """
        Register a callback for progress updates.

        Args:
            upload_id: Upload identifier
            callback: Async function(ProgressUpdate) to call on updates
        """
        if upload_id not in self.callbacks:
            self.callbacks[upload_id] = []
        self.callbacks[upload_id].append(callback)

    async def _notify_callbacks(self, upload_id: str, update: ProgressUpdate) -> None:
        """Notify all registered callbacks of progress update."""
        if upload_id not in self.callbacks:
            return

        callbacks = self.callbacks[upload_id]
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Error in callback for {upload_id}: {e}")

    async def _cleanup_upload(self, upload_id: str) -> None:
        """Clean up upload tracking after a delay."""
        # Keep upload info for 5 minutes for client queries
        async def cleanup():
            await asyncio.sleep(300)  # 5 minutes
            async with self.lock:
                if upload_id in self.uploads:
                    del self.uploads[upload_id]
                if upload_id in self.callbacks:
                    del self.callbacks[upload_id]

        asyncio.create_task(cleanup())

    def get_progress(self, upload_id: str) -> Optional[Dict]:
        """
        Get current progress for an upload.

        Args:
            upload_id: Upload identifier

        Returns:
            Progress dict or None if not found
        """
        if upload_id not in self.uploads:
            return None

        upload = self.uploads[upload_id]
        total_chunks = upload["total_chunks"]
        current_chunk = upload["current_chunk"]

        return {
            "upload_id": upload_id,
            "status": upload["status"].value,
            "progress_percent": (current_chunk / total_chunks * 100)
            if total_chunks > 0
            else 0,
            "current_chunk": current_chunk,
            "total_chunks": total_chunks,
        }


# Global progress tracker instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create global progress tracker."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
