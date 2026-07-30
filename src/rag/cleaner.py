"""
rag/cleaner.py — Text cleaning and normalization.

Removes noise introduced by PDF/DOCX extraction:
- Repeated headers/footers
- Control characters
- Excessive whitespace
Preserves medical terminology and structure.
"""

from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Apply the full cleaning pipeline to raw extracted text.

    Steps:
        1. Unicode normalization (NFKC)
        2. Remove control characters (except newline and tab)
        3. Collapse excessive blank lines (>2 → 2)
        4. Strip leading/trailing whitespace per line
        5. Collapse multiple spaces on the same line
        6. Strip overall leading/trailing whitespace

    Args:
        text: Raw text from a document loader.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # 1. Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove control characters (keep \n and \t)
    text = re.sub(r"[^\S\n\t ]+", " ", text)          # collapse weird spaces
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Normalise Windows line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Strip each line independently
    lines = [line.strip() for line in text.split("\n")]

    # 5. Collapse runs of more than 2 blank lines into exactly 2
    cleaned_lines: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count < 2:   # allow at most 1 blank line between paragraphs
                cleaned_lines.append("")
        else:
            blank_count = 0
            # Collapse multiple spaces within the line
            cleaned_lines.append(re.sub(r" {2,}", " ", line))

    text = "\n".join(cleaned_lines)

    # 6. Final strip
    return text.strip()


def remove_repeated_header_footer(
    text: str,
    min_occurrences: int = 3,
    max_line_length: int = 120,
) -> str:
    """
    Heuristically remove lines that appear many times (likely headers/footers).

    A line is considered a repeated header/footer if:
    - It appears at least *min_occurrences* times in the document.
    - Its length is <= *max_line_length* (long paragraphs are kept).
    - It is not purely whitespace.

    Args:
        text: Cleaned document text.
        min_occurrences: Minimum repeat count to trigger removal.
        max_line_length: Lines longer than this are never removed.

    Returns:
        Text with suspected header/footer lines removed.
    """
    lines = text.split("\n")

    # Count occurrences of each non-empty short line
    from collections import Counter
    line_counts = Counter(
        line for line in lines
        if line.strip() and len(line) <= max_line_length
    )

    # Build a set of lines to remove
    repeated = {
        line for line, count in line_counts.items()
        if count >= min_occurrences
    }

    filtered = [line for line in lines if line not in repeated]
    return "\n".join(filtered)


def normalize_medical_whitespace(text: str) -> str:
    """
    Ensure medical abbreviations and bullet points are not broken across lines.

    E.g. "e.g.\n treatment" → "e.g. treatment"
    """
    # Join lines that end mid-sentence (no period, no colon)
    text = re.sub(r"(?<![.!?:•\-])\n(?=[a-z])", " ", text)
    return text


def full_clean(text: str) -> str:
    """
    Convenience wrapper that applies all cleaning steps in order.

    Pipeline:
        clean_text → remove_repeated_header_footer → normalize_medical_whitespace
    """
    text = clean_text(text)
    text = remove_repeated_header_footer(text)
    text = normalize_medical_whitespace(text)
    return text
