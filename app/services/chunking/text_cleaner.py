import re
from typing import Optional
from app.services.chunking.base import BaseTextCleaner


class TextCleaner(BaseTextCleaner):
    """
    Production-grade OCR text cleaner for Driving Licence and structured documents.
    Normalizes whitespace and line endings without altering domain specific data (DL numbers, dates, names).
    """

    def clean_text(self, text: Optional[str]) -> str:
        """
        Cleans and normalizes OCR raw text:
        1. Returns "" if input is None, empty, or whitespace-only.
        2. Normalizes carriage returns and line endings to '\\n'.
        3. Replaces multiple horizontal spaces/tabs on each line with a single space.
        4. Trims trailing whitespace on individual lines.
        5. Collapses 3 or more consecutive newlines into double newlines ('\\n\\n').
        6. Strips leading and trailing outer document whitespace.
        """
        if not text:
            return ""

        # Step 1: Normalize line endings
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Step 2: Normalize inline horizontal spaces & tabs (preserve newlines)
        lines = []
        for line in normalized.split("\n"):
            # Replace multiple inline spaces/tabs with single space
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(cleaned_line)

        rejoined = "\n".join(lines)

        # Step 3: Collapse excessive blank lines (max 2 consecutive newlines)
        collapsed = re.sub(r"\n{3,}", "\n\n", rejoined)

        # Step 4: Final strip of leading/trailing whitespace
        return collapsed.strip()


def get_text_cleaner() -> BaseTextCleaner:
    """
    Factory function returning active TextCleaner instance.
    """
    return TextCleaner()
