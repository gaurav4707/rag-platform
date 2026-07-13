"""Default benchmark questions.

This module provides a small, deterministic set of questions for benchmarking.
Users can replace these by providing a custom questions file (one question per line).
"""

DEFAULT_QUESTIONS: list[str] = [
    "What is this document about?",
    "Summarize the document.",
    "List the major topics covered.",
    "What conclusions are presented?",
    "Who are the key people mentioned?",
]

MAX_QUESTIONS: int = 10


def load_questions(file_path: str | None = None, max_questions: int = MAX_QUESTIONS) -> list[str]:
    """Load benchmark questions from a file or use defaults.

    Args:
        file_path: Optional path to a text file with one question per line.
        max_questions: Maximum number of questions to return (capped at MAX_QUESTIONS).

    Returns:
        List of questions to use for benchmarking.
    """
    if file_path:
        with open(file_path, "r") as f:
            questions = [line.strip() for line in f if line.strip()]
    else:
        questions = DEFAULT_QUESTIONS

    # Enforce maximum
    return questions[: min(max_questions, MAX_QUESTIONS)]


def save_questions(questions: list[str], file_path: str) -> None:
    """Save questions to a file (one per line)."""
    with open(file_path, "w") as f:
        for q in questions:
            f.write(q + "\n")