"""
Text Processing Utilities Module

Provides helper functions for text cleaning and string manipulation.
"""

import re


def clean_raw_text(text: str) -> str:
    """
    Cleans raw OCR text by removing redundant blank lines, control characters, and leading/trailing whitespace.

    Args:
        text: Raw OCR extracted text string.

    Returns:
        Cleaned text string suitable for chunking and embedding.
    """
    if not text:
        return ""
    # Normalize newline characters
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace 3 or more consecutive newlines with 2 newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Strip leading/trailing whitespace
    return cleaned.strip()
