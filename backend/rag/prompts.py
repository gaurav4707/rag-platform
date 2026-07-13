"""Prompt Builder module for Agentic RAG.

Responsible for constructing prompts from retrieved context.
Never performs retrieval - only formats retrieved context for the LLM.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from backend.models.rag_models import RetrievalResult, RetrievedChunk
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


@dataclass
class PromptConfig:
    """Configuration for prompt building."""
    max_context_chars: int = 8000
    max_chunks: int = 6


DEFAULT_PROMPT_CONFIG = PromptConfig()


def _remove_duplicate_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Remove duplicate chunks based on content equality.

    Preserves the first occurrence (highest rank) of each unique chunk.
    Only uses exact text matching - no semantic deduplication.
    """
    seen_content: set[str] = set()
    unique_chunks: list[RetrievedChunk] = []
    duplicates_removed = 0

    for chunk in chunks:
        content_key = chunk.document.page_content.strip()
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_chunks.append(chunk)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.debug("Duplicate chunks removed: %d", duplicates_removed)

    return unique_chunks


def _truncate_context(chunks: list[RetrievedChunk], max_chars: int) -> list[RetrievedChunk]:
    """Truncate context to fit within character budget.

    Keeps highest-ranked chunks (preserves retrieval order).
    Never truncates individual chunks - only removes from the end.
    """
    if not chunks:
        return chunks

    total_chars = sum(len(chunk.document.page_content) for chunk in chunks)

    if total_chars <= max_chars:
        return chunks

    truncated: list[RetrievedChunk] = []
    current_chars = 0

    for chunk in chunks:
        chunk_chars = len(chunk.document.page_content)
        if current_chars + chunk_chars > max_chars:
            break
        truncated.append(chunk)
        current_chars += chunk_chars

    removed = len(chunks) - len(truncated)
    if removed > 0:
        logger.debug("Context truncated: removed %d chunks to fit within %d characters",
                    removed, max_chars)

    return truncated


def _format_chunk_metadata(chunk: RetrievedChunk, source_number: int) -> str:
    """Format chunk metadata for prompt display.

    Shows user-friendly metadata only - no internal IDs.
    """
    meta = chunk.document.metadata

    filename = meta.get("filename", "unknown")
    page = meta.get("page", "unknown")
    chunk_index = meta.get("chunk_index", "unknown")
    score = chunk.score

    lines = [
        f"[Source {source_number}]",
        f"Document: {filename}",
        f"Page: {page}",
        f"Chunk: {chunk_index}",
    ]

    if score is not None:
        lines.append(f"Relevance Score: {score:.4f}")

    return "\n".join(lines)


def _format_chunk_content(chunk: RetrievedChunk) -> str:
    """Format chunk content for prompt."""
    content = chunk.document.page_content.strip()
    return f"Content:\n{content}"


def _format_retrieved_chunk(chunk: RetrievedChunk, source_number: int) -> str:
    """Format a single retrieved chunk with metadata and content."""
    metadata_section = _format_chunk_metadata(chunk, source_number)
    content_section = _format_chunk_content(chunk)

    return f"{metadata_section}\n\n{content_section}"


def build_system_prompt() -> str:
    """Build the SYSTEM INSTRUCTIONS section.

    Contains grounding rules, citation guidance, and behavior instructions.
    Provider-agnostic - no model-specific formatting.
    """
    return """========================
SYSTEM INSTRUCTIONS
========================

You are a Retrieval-Augmented Generation assistant specialized in answering questions using provided document context.

GROUNDING RULES:
- Answer ONLY using the provided retrieved context.
- If the answer cannot be determined from the context, clearly state: "I don't know based on the available documents."
- Do not fabricate, infer, or hallucinate facts not present in the context.
- Prefer precise, direct answers over speculative ones.
- When multiple sources provide relevant information, synthesize them while preserving attribution.
- Preserve technical terminology and specific details from the source documents.

CITATION GUIDANCE:
- When information comes from multiple retrieved sources, synthesize the answer while preserving attribution.
- Reference sources naturally in your response (e.g., "According to Document X..." or "Source 1 states...").
- Do not reference internal chunk IDs or metadata fields not shown to you.
- You do not need to cite every sentence, but key claims should be attributable to the provided sources.

BEHAVIOR:
- Be concise but complete.
- Explain concepts in your own words - do not copy large passages verbatim.
- Ignore irrelevant retrieved passages.
- If the question is ambiguous, ask for clarification rather than guessing."""


def build_user_question_section(question: str) -> str:
    """Build the USER QUESTION section."""
    return f"""========================
USER QUESTION
========================

{question}"""


def build_context_section(retrieval_result: RetrievalResult) -> str:
    """Build the RETRIEVED CONTEXT section.

    Processes chunks: deduplication, truncation, formatting.
    """
    chunks = retrieval_result.chunks

    logger.debug("Chunks received: %d", len(chunks))

    # Remove duplicate chunks (exact content match)
    unique_chunks = _remove_duplicate_chunks(chunks)

    # Truncate to fit context window (preserves ranking order)
    config = DEFAULT_PROMPT_CONFIG
    final_chunks = _truncate_context(unique_chunks, config.max_context_chars)

    logger.debug("Final chunks for prompt: %d", len(final_chunks))
    logger.debug("Prompt context length: %d characters",
                 sum(len(c.document.page_content) for c in final_chunks))

    if not final_chunks:
        return """========================
RETRIEVED CONTEXT
========================

No relevant context retrieved."""

    # Format each chunk with clear separation
    formatted_chunks = []
    for i, chunk in enumerate(final_chunks, 1):
        formatted = _format_retrieved_chunk(chunk, i)
        formatted_chunks.append(formatted)

    # Join with clear separator
    separator = "\n" + "-" * 50 + "\n"
    context_content = separator.join(formatted_chunks)

    return f"""========================
RETRIEVED CONTEXT
========================

{context_content}"""


def build_final_instruction() -> str:
    """Build the final ANSWER instruction."""
    return """========================
ANSWER
========================

Provide your answer based on the retrieved context above."""


def build_prompt(question: str, retrieval_result: RetrievalResult) -> str:
    """Build the complete prompt for the LLM.

    This is the main entry point for prompt construction.

    Args:
        question: The user's original question.
        retrieval_result: The RetrievalResult from the retriever containing
            ranked chunks and metadata.

    Returns:
        A formatted prompt string ready for the LLM.

    Prompt structure:
    1. SYSTEM INSTRUCTIONS - Grounding rules, citation guidance, behavior
    2. USER QUESTION - The original user question
    3. RETRIEVED CONTEXT - Formatted chunks with metadata
    4. ANSWER - Instruction to generate the response

    Provider-agnostic: produces plain text that works with any chat model.
    """
    logger.debug("Building prompt for question: %s", question[:100])

    system_prompt = build_system_prompt()
    user_question = build_user_question_section(question)
    context_section = build_context_section(retrieval_result)
    final_instruction = build_final_instruction()

    prompt = "\n\n".join([
        system_prompt,
        user_question,
        context_section,
        final_instruction,
    ])

    logger.debug("Final prompt length: %d characters", len(prompt))

    return prompt