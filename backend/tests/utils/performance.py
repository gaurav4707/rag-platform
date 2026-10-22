"""Performance tracking utilities for streaming chat endpoints."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Configure performance logger
performance_logger = logging.getLogger("performance")
performance_logger.setLevel(logging.INFO)

# Add handler if not already present
if not performance_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    performance_logger.addHandler(handler)
    # Prevent propagation to root logger to avoid duplicate logs
    performance_logger.propagate = False


class CompletionStatus(Enum):
    """Completion status of a streaming request."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class StreamPerformanceTracker:
    """Tracks end-to-end streaming latency metrics.

    Uses time.perf_counter() for high-precision timing.
    Stores timestamps internally as floating-point seconds.
    Converts to milliseconds only when logging.
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    _start_time: Optional[float] = field(default=None, init=False)
    _first_token_time: Optional[float] = field(default=None, init=False)
    _end_time: Optional[float] = field(default=None, init=False)
    _chunk_count: int = field(default=0, init=False)
    _status: CompletionStatus = field(default=CompletionStatus.SUCCESS, init=False)
    _error: Optional[Exception] = field(default=None, init=False)

    def start(self) -> None:
        """Record the request start timestamp."""
        self._start_time = time.perf_counter()
        self._first_token_time = None
        self._end_time = None
        self._chunk_count = 0
        self._status = CompletionStatus.SUCCESS
        self._error = None

    def mark_first_token(self) -> None:
        """Record the timestamp of the first token being streamed."""
        if self._first_token_time is None and self._start_time is not None:
            self._first_token_time = time.perf_counter()

    def increment_chunks(self, count: int = 1) -> None:
        """Increment the chunk counter."""
        self._chunk_count += count

    def finish_success(self) -> None:
        """Mark the stream as completed successfully."""
        self._end_time = time.perf_counter()
        self._status = CompletionStatus.SUCCESS
        self._log_metrics()

    def finish_error(self, error: Exception) -> None:
        """Mark the stream as failed with an error."""
        self._end_time = time.perf_counter()
        self._status = CompletionStatus.ERROR
        self._error = error
        self._log_metrics()

    def finish_cancelled(self) -> None:
        """Mark the stream as cancelled (client disconnected)."""
        self._end_time = time.perf_counter()
        self._status = CompletionStatus.CANCELLED
        self._log_metrics()

    @property
    def ttft_ms(self) -> Optional[float]:
        """Time to first token in milliseconds."""
        if self._first_token_time is not None and self._start_time is not None:
            return (self._first_token_time - self._start_time) * 1000
        return None

    @property
    def total_duration_ms(self) -> Optional[float]:
        """Total response duration in milliseconds."""
        if self._end_time is not None and self._start_time is not None:
            return (self._end_time - self._start_time) * 1000
        return None

    @property
    def chunk_count(self) -> int:
        """Number of chunks/tokens streamed."""
        return self._chunk_count

    @property
    def status(self) -> CompletionStatus:
        """Completion status of the stream."""
        return self._status

    @property
    def error(self) -> Optional[Exception]:
        """Error if the stream failed."""
        return self._error

    def _log_metrics(self) -> None:
        """Log performance metrics."""
        ttft = self.ttft_ms
        total = self.total_duration_ms

        performance_logger.info(
            "Request: %s | TTFT: %s | Total Duration: %s | Chunks: %d | Status: %s",
            self.request_id,
            f"{ttft:.2f} ms" if ttft is not None else "N/A",
            f"{total:.2f} ms" if total is not None else "N/A",
            self._chunk_count,
            self._status.value,
        )

        if self._status == CompletionStatus.ERROR and self._error:
            performance_logger.error(
                "Request: %s | Error: %s",
                self.request_id,
                str(self._error),
            )