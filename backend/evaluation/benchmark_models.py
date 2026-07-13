"""Data models for benchmark results."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class RequestStatus(Enum):
    """Status of a benchmark request."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass
class UploadResult:
    """Result of the PDF upload and indexing operation."""

    file_size_mb: float
    page_count: Optional[int]
    indexing_duration_seconds: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ChatResult:
    """Result of a single chat benchmark request."""

    question: str
    ttft_ms: Optional[float] = None
    total_duration_ms: Optional[float] = None
    chunk_count: int = 0
    status: RequestStatus = RequestStatus.SUCCESS
    error_message: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Aggregated statistics across all chat requests."""

    total_questions: int
    successful: int
    failed: int
    average_ttft_ms: Optional[float]
    average_duration_ms: Optional[float]
    fastest_duration_ms: Optional[float]
    slowest_duration_ms: Optional[float]
    median_duration_ms: Optional[float]


@dataclass
class BenchmarkReport:
    """Complete benchmark report containing all results."""

    timestamp: datetime = field(default_factory=datetime.now)
    backend_url: str = ""
    llm_provider: str = "Unknown"
    embedding_model: str = "Unknown"
    upload_result: Optional[UploadResult] = None
    chat_results: list[ChatResult] = field(default_factory=list)
    summary: Optional[BenchmarkSummary] = None

    def to_dict(self) -> dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "backend_url": self.backend_url,
            "llm_provider": self.llm_provider,
            "embedding_model": self.embedding_model,
            "upload_result": (
                {
                    "file_size_mb": self.upload_result.file_size_mb,
                    "page_count": self.upload_result.page_count,
                    "indexing_duration_seconds": self.upload_result.indexing_duration_seconds,
                    "success": self.upload_result.success,
                    "error_message": self.upload_result.error_message,
                }
                if self.upload_result
                else None
            ),
            "chat_results": [
                {
                    "question": r.question,
                    "ttft_ms": r.ttft_ms,
                    "total_duration_ms": r.total_duration_ms,
                    "chunk_count": r.chunk_count,
                    "status": r.status.value,
                    "error_message": r.error_message,
                }
                for r in self.chat_results
            ],
            "summary": (
                {
                    "total_questions": self.summary.total_questions,
                    "successful": self.summary.successful,
                    "failed": self.summary.failed,
                    "average_ttft_ms": self.summary.average_ttft_ms,
                    "average_duration_ms": self.summary.average_duration_ms,
                    "fastest_duration_ms": self.summary.fastest_duration_ms,
                    "slowest_duration_ms": self.summary.slowest_duration_ms,
                    "median_duration_ms": self.summary.median_duration_ms,
                }
                if self.summary
                else None
            ),
        }

    def save_json(self, path: str | Path) -> None:
        """Save report as JSON file."""
        import json

        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    def save_markdown(self, path: str | Path) -> None:
        """Save report as Markdown file."""
        lines = [
            "# Benchmark Report",
            "",
            "## Environment",
            f"- **Backend URL**: {self.backend_url}",
            f"- **LLM Provider**: {self.llm_provider}",
            f"- **Embedding Model**: {self.embedding_model}",
            f"- **Timestamp**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Upload",
        ]

        if self.upload_result:
            lines.extend([
                f"- **File Size**: {self.upload_result.file_size_mb:.2f} MB",
                f"- **Page Count**: {self.upload_result.page_count if self.upload_result.page_count else 'N/A'}",
                f"- **Indexing Time**: {self.upload_result.indexing_duration_seconds:.2f} s",
                f"- **Status**: {'Success' if self.upload_result.success else 'Failed'}",
            ])
            if self.upload_result.error_message:
                lines.append(f"- **Error**: {self.upload_result.error_message}")
        else:
            lines.append("- **Status**: Not performed")

        lines.extend(["", "---", "", "## Chat"])

        if self.summary:
            lines.extend([
                f"- **Questions**: {self.summary.total_questions}",
                f"- **Successful**: {self.summary.successful}",
                f"- **Failed**: {self.summary.failed}",
                f"- **Average TTFT**: {self.summary.average_ttft_ms:.1f} ms"
                if self.summary.average_ttft_ms
                else "- **Average TTFT**: N/A",
                f"- **Average Duration**: {self.summary.average_duration_ms / 1000:.2f} s"
                if self.summary.average_duration_ms
                else "- **Average Duration**: N/A",
                f"- **Fastest**: {self.summary.fastest_duration_ms / 1000:.2f} s"
                if self.summary.fastest_duration_ms
                else "- **Fastest**: N/A",
                f"- **Slowest**: {self.summary.slowest_duration_ms / 1000:.2f} s"
                if self.summary.slowest_duration_ms
                else "- **Slowest**: N/A",
                f"- **Median Duration**: {self.summary.median_duration_ms / 1000:.2f} s"
                if self.summary.median_duration_ms
                else "- **Median Duration**: N/A",
            ])

        lines.extend(["", "---", "", "## Individual Results", ""])

        for i, result in enumerate(self.chat_results, 1):
            lines.extend([
                f"### Question {i}",
                f"- **Question**: {result.question}",
                f"- **TTFT**: {result.ttft_ms:.1f} ms" if result.ttft_ms else "- **TTFT**: N/A",
                f"- **Duration**: {result.total_duration_ms / 1000:.2f} s" if result.total_duration_ms else "- **Duration**: N/A",
                f"- **Chunks**: {result.chunk_count}",
                f"- **Status**: {result.status.value}",
                "",
            ])
            if result.error_message:
                lines.append(f"- **Error**: {result.error_message}")
                lines.append("")

        lines.extend(["---", "", "## Overall", ""])

        if self.summary and self.summary.failed == 0:
            lines.append("**PASS**")
        elif self.summary and self.summary.successful > 0:
            lines.append("**PARTIAL**")
        else:
            lines.append("**FAIL**")

        Path(path).write_text("\n".join(lines))