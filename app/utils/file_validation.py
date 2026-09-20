"""
File Validation Utilities Module

Provides helper functions for sanitizing filenames, validating extensions, and inferring MIME types.
"""

import os
import re
import mimetypes
from typing import Tuple

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user input filename to prevent path traversal and object storage key errors.

    Args:
        filename: Raw user filename string.

    Returns:
        Cleaned, safe filename string.
    """
    basename = os.path.basename(filename.strip())
    name_part, ext = os.path.splitext(basename)
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_part)
    safe_ext = ext.lower()
    return f"{safe_name}{safe_ext}"


def validate_file_extension(filename: str) -> bool:
    """
    Verifies that the file extension matches allowed document formats (.pdf, .jpg, .jpeg, .png).

    Args:
        filename: Input filename string.

    Returns:
        True if extension is allowed, False otherwise.
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def guess_mime_type(filename: str) -> str:
    """
    Infers MIME type string from a filename.

    Args:
        filename: Input filename.

    Returns:
        MIME type string (e.g. 'application/pdf', 'image/jpeg', 'image/png').
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type

    ext = filename.lower()
    if ext.endswith(".pdf"):
        return "application/pdf"
    elif ext.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif ext.endswith(".png"):
        return "image/png"

    return "application/octet-stream"
