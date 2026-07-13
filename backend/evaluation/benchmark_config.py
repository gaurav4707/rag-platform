"""Benchmark configuration settings."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for the benchmark runner.

    Attributes:
        backend_url: Base URL of the running backend API.
        delay_between_requests: Seconds to wait between sequential requests.
        max_questions: Maximum number of questions to benchmark.
        output_dir: Directory where reports will be saved.
        request_timeout: Timeout in seconds for HTTP requests.
        pdf_path: Path to the PDF file to benchmark with.
        custom_questions_file: Optional path to a custom questions file.
    """

    backend_url: str = "http://localhost:8000"
    delay_between_requests: float = 1.0
    max_questions: int = 5
    output_dir: Path = field(default_factory=lambda: Path("benchmark_output"))
    request_timeout: int = 60
    pdf_path: Optional[Path] = None
    custom_questions_file: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_questions < 1:
            raise ValueError("max_questions must be at least 1")
        if self.max_questions > 10:
            raise ValueError("max_questions cannot exceed 10 (rate limit protection)")
        if self.delay_between_requests < 0:
            raise ValueError("delay_between_requests cannot be negative")
        if self.request_timeout < 1:
            raise ValueError("request_timeout must be at least 1 second")
        if self.pdf_path is not None and not self.pdf_path.exists():
            raise ValueError(f"PDF file not found: {self.pdf_path}")
        if self.custom_questions_file is not None and not self.custom_questions_file.exists():
            raise ValueError(f"Custom questions file not found: {self.custom_questions_file}")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)


def load_config_from_env() -> BenchmarkConfig:
    """Load benchmark configuration from environment variables.

    Supports:
        BENCHMARK_BACKEND_URL
        BENCHMARK_DELAY
        BENCHMARK_MAX_QUESTIONS
        BENCHMARK_OUTPUT_DIR
        BENCHMARK_TIMEOUT
        BENCHMARK_PDF_PATH
        BENCHMARK_QUESTIONS_FILE

    Returns:
        BenchmarkConfig with values from environment or defaults.
    """
    import os

    return BenchmarkConfig(
        backend_url=os.getenv("BENCHMARK_BACKEND_URL", "http://localhost:8000"),
        delay_between_requests=float(os.getenv("BENCHMARK_DELAY", "1.0")),
        max_questions=int(os.getenv("BENCHMARK_MAX_QUESTIONS", "5")),
        output_dir=Path(os.getenv("BENCHMARK_OUTPUT_DIR", "benchmark_output")),
        request_timeout=int(os.getenv("BENCHMARK_TIMEOUT", "60")),
        # Safely construct Path objects only when environment variables are set and non-empty.
        pdf_path=(Path(p) if (p := os.getenv("BENCHMARK_PDF_PATH")) is not None and p != "" else None),
        custom_questions_file=(
            Path(q) if (q := os.getenv("BENCHMARK_QUESTIONS_FILE")) is not None and q != "" else None
        ),
    )