"""Benchmark runner for RAG chat endpoint.

This module provides a command-line tool to run automated benchmarks
against the /chat endpoint, measuring latency, throughput, and success rates.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


@dataclass
class BenchmarkResult:
    """Result of a single benchmark request."""

    question: str
    success: bool
    status_code: Optional[int] = None
    ttft_ms: Optional[float] = None
    total_duration_ms: Optional[float] = None
    chunk_count: int = 0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class BenchmarkSummary:
    """Summary statistics for a benchmark run."""

    total: int = 0
    successful: int = 0
    failed: int = 0
    avg_ttft_ms: Optional[float] = None
    avg_total_ms: Optional[float] = None
    min_ttft_ms: Optional[float] = None
    max_ttft_ms: Optional[float] = None
    total_chunks: int = 0


async def run_single_benchmark(
    client: httpx.AsyncClient,
    base_url: str,
    question: str,
    timeout: float = 60.0,
) -> BenchmarkResult:
    """Execute a single benchmark request against /chat/stream.

    Measures:
    - Time to First Token (TTFT)
    - Total response duration
    - Number of chunks streamed
    - Success/failure status

    Args:
        client: Async HTTP client.
        base_url: Base URL of the API (e.g., http://localhost:8000).
        question: Question to ask.
        timeout: Request timeout in seconds.

    Returns:
        BenchmarkResult with timing metrics.
    """
    url = f"{base_url.rstrip('/')}/chat/stream"
    payload = {"message": question}

    start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    chunk_count = 0
    error_msg: Optional[str] = None

    try:
        async with client.stream(
            "POST",
            url,
            json=payload,
            timeout=timeout,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            status_code = response.status_code

            async for line in response.aiter_lines():
                current_time = time.perf_counter()

                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str.strip():
                        try:
                            data = json.loads(data_str)
                            if "token" in data:
                                if first_token_time is None:
                                    first_token_time = current_time
                                chunk_count += 1
                            elif data.get("done"):
                                # Final message with sources - don't count as chunk
                                pass
                        except json.JSONDecodeError:
                            pass

    except httpx.TimeoutException:
        error_msg = f"Request timed out after {timeout}s"
        status_code = None
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        status_code = e.response.status_code
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        status_code = None

    end_time = time.perf_counter()
    total_duration_ms = (end_time - start_time) * 1000

    ttft_ms = None
    if first_token_time is not None:
        ttft_ms = (first_token_time - start_time) * 1000

    return BenchmarkResult(
        question=question,
        success=error_msg is None,
        status_code=status_code,
        ttft_ms=ttft_ms,
        total_duration_ms=total_duration_ms,
        chunk_count=chunk_count,
        error=error_msg,
    )


async def run_benchmark(
    base_url: str,
    questions: list[str],
    concurrency: int = 1,
    timeout: float = 60.0,
    delay_between: float = 0.0,
) -> tuple[list[BenchmarkResult], BenchmarkSummary]:
    """Run a full benchmark suite.

    Args:
        base_url: Base URL of the API.
        questions: List of questions to benchmark.
        concurrency: Number of concurrent requests (1 = sequential).
        timeout: Request timeout in seconds.
        delay_between: Delay between requests in seconds (sequential only).

    Returns:
        Tuple of (results list, summary statistics).
    """
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    timeout_config = httpx.Timeout(timeout, connect=5.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout_config) as client:
        if concurrency <= 1:
            # Sequential execution
            results = []
            for i, question in enumerate(questions):
                if i > 0 and delay_between > 0:
                    await asyncio.sleep(delay_between)
                result = await run_single_benchmark(client, base_url, question, timeout)
                results.append(result)
        else:
            # Concurrent execution
            semaphore = asyncio.Semaphore(concurrency)

            async def bounded_request(q: str) -> BenchmarkResult:
                async with semaphore:
                    return await run_single_benchmark(client, base_url, q, timeout)

            results = await asyncio.gather(*[bounded_request(q) for q in questions])

    # Calculate summary
    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    ttfts = [r.ttft_ms for r in successful_results if r.ttft_ms is not None]
    totals = [r.total_duration_ms for r in successful_results if r.total_duration_ms is not None]

    summary = BenchmarkSummary(
        total=len(results),
        successful=len(successful_results),
        failed=len(failed_results),
        avg_ttft_ms=sum(ttfts) / len(ttfts) if ttfts else None,
        avg_total_ms=sum(totals) / len(totals) if totals else None,
        min_ttft_ms=min(ttfts) if ttfts else None,
        max_ttft_ms=max(ttfts) if ttfts else None,
        total_chunks=sum(r.chunk_count for r in results),
    )

    return results, summary


def print_results(results: list[BenchmarkResult], summary: BenchmarkSummary) -> None:
    """Print benchmark results to console."""
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        status = "✓" if result.success else "✗"
        ttft = f"{result.ttft_ms:.1f}ms" if result.ttft_ms else "N/A"
        total = f"{result.total_duration_ms:.1f}ms" if result.total_duration_ms else "N/A"
        chunks = result.chunk_count

        print(f"\n[{i}] {status} {result.question[:60]}{'...' if len(result.question) > 60 else ''}")
        print(f"    TTFT: {ttft} | Total: {total} | Chunks: {chunks}")
        if result.error:
            print(f"    Error: {result.error}")

    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"Total Requests:     {summary.total}")
    print(f"Successful:         {summary.successful}")
    print(f"Failed:             {summary.failed}")
    print(f"Success Rate:       {summary.successful / summary.total * 100:.1f}%" if summary.total > 0 else "N/A")

    if summary.avg_ttft_ms:
        print(f"Avg TTFT:           {summary.avg_ttft_ms:.1f}ms")
    if summary.avg_total_ms:
        print(f"Avg Total Duration: {summary.avg_total_ms:.1f}ms")
    if summary.min_ttft_ms:
        print(f"Min TTFT:           {summary.min_ttft_ms:.1f}ms")
    if summary.max_ttft_ms:
        print(f"Max TTFT:           {summary.max_ttft_ms:.1f}ms")
    print(f"Total Chunks:       {summary.total_chunks}")


def save_results(
    results: list[BenchmarkResult],
    summary: BenchmarkSummary,
    output_dir: Path,
    questions_file: Optional[str] = None,
) -> tuple[Path, Path]:
    """Save benchmark results to JSON and summary files.

    Args:
        results: List of benchmark results.
        summary: Summary statistics.
        output_dir: Directory to save files.
        questions_file: Path to questions file used (for reference).

    Returns:
        Tuple of (json_path, summary_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"benchmark_{timestamp}.json"
    summary_path = output_dir / f"benchmark_{timestamp}_summary.txt"

    # Save detailed JSON
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "questions_file": questions_file,
        "summary": {
            "total": summary.total,
            "successful": summary.successful,
            "failed": summary.failed,
            "success_rate": summary.successful / summary.total if summary.total > 0 else 0,
            "avg_ttft_ms": summary.avg_ttft_ms,
            "avg_total_ms": summary.avg_total_ms,
            "min_ttft_ms": summary.min_ttft_ms,
            "max_ttft_ms": summary.max_ttft_ms,
            "total_chunks": summary.total_chunks,
        },
        "results": [
            {
                "question": r.question,
                "success": r.success,
                "status_code": r.status_code,
                "ttft_ms": r.ttft_ms,
                "total_duration_ms": r.total_duration_ms,
                "chunk_count": r.chunk_count,
                "error": r.error,
                "timestamp": r.timestamp,
            }
            for r in results
        ],
    }

    json_path.write_text(json.dumps(data, indent=2))

    # Save human-readable summary
    lines = [
        f"Benchmark Run: {data['timestamp']}",
        f"Questions File: {questions_file or 'default'}",
        "",
        f"Total Requests: {summary.total}",
        f"Successful: {summary.successful}",
        f"Failed: {summary.failed}",
        f"Success Rate: {summary.successful / summary.total * 100:.1f}%" if summary.total > 0 else "N/A",
        "",
    ]

    if summary.avg_ttft_ms:
        lines.append(f"Avg TTFT: {summary.avg_ttft_ms:.1f}ms")
    if summary.avg_total_ms:
        lines.append(f"Avg Total Duration: {summary.avg_total_ms:.1f}ms")
    if summary.min_ttft_ms:
        lines.append(f"Min TTFT: {summary.min_ttft_ms:.1f}ms")
    if summary.max_ttft_ms:
        lines.append(f"Max TTFT: {summary.max_ttft_ms:.1f}ms")
    lines.append(f"Total Chunks: {summary.total_chunks}")
    lines.append("")
    lines.append("Per-Request Results:")

    for i, r in enumerate(results, 1):
        status = "PASS" if r.success else "FAIL"
        ttft = f"{r.ttft_ms:.1f}ms" if r.ttft_ms else "N/A"
        total = f"{r.total_duration_ms:.1f}ms" if r.total_duration_ms else "N/A"
        lines.append(f"  {i}. [{status}] {r.question[:80]}")
        lines.append(f"     TTFT: {ttft} | Total: {total} | Chunks: {r.chunk_count}")
        if r.error:
            lines.append(f"     Error: {r.error}")

    summary_path.write_text("\n".join(lines))

    return json_path, summary_path


def main() -> int:
    """Main entry point for benchmark CLI."""
    parser = argparse.ArgumentParser(
        description="Run benchmark against RAG chat endpoint",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API",
    )
    parser.add_argument(
        "--questions",
        "-q",
        default=None,
        help="Path to questions file (one per line)",
    )
    parser.add_argument(
        "--max-questions",
        "-n",
        type=int,
        default=5,
        help="Maximum number of questions to run",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=1,
        help="Number of concurrent requests",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=60.0,
        help="Request timeout in seconds",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.0,
        help="Delay between sequential requests (seconds)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("benchmark_results"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file",
    )

    args = parser.parse_args()

    # Load questions
    sys.path.insert(0, str(Path(__file__).parent))
    from sample_questions import load_questions

    questions = load_questions(args.questions, args.max_questions)

    if not questions:
        print("Error: No questions to run", file=sys.stderr)
        return 1

    print(f"Running benchmark with {len(questions)} question(s)...")
    print(f"Target: {args.url}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Timeout: {args.timeout}s")

    # Run benchmark
    results, summary = asyncio.run(
        run_benchmark(
            base_url=args.url,
            questions=questions,
            concurrency=args.concurrency,
            timeout=args.timeout,
            delay_between=args.delay,
        )
    )

    # Print results
    print_results(results, summary)

    # Save results
    if not args.no_save:
        json_path, summary_path = save_results(results, summary, args.output, args.questions)
        print(f"\nResults saved to:")
        print(f"  {json_path}")
        print(f"  {summary_path}")

    # Exit with error code if any failures
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())