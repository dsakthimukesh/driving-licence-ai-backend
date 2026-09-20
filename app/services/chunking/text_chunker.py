import logging
from typing import List, Optional

from app.core.config import settings
from app.services.chunking.base import BaseTextChunker, ChunkPayload
from app.services.ocr.models import OCRPageResult

logger = logging.getLogger(__name__)


class TextChunker(BaseTextChunker):
    """
    Configurable sliding-window text chunker with word boundary snapping and page metadata tracking.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

        if self.chunk_size <= 0:
            raise ValueError(f"CHUNK_SIZE must be positive, got {self.chunk_size}")
        if self.chunk_overlap < 0:
            raise ValueError(f"CHUNK_OVERLAP must be non-negative, got {self.chunk_overlap}")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({self.chunk_overlap}) must be strictly smaller than CHUNK_SIZE ({self.chunk_size})."
            )

    def split_into_chunks(
        self,
        text: str,
        page_number: Optional[int] = None,
        pages: Optional[List[OCRPageResult]] = None
    ) -> List[ChunkPayload]:
        """
        Splits cleaned OCR text into structured overlapping ChunkPayload objects.
        
        If `pages` list contains per-page OCR output, chunks each page independently
        while maintaining global chronological chunk_index values.
        """
        if pages and len(pages) > 0 and any(p.text.strip() for p in pages):
            all_chunks: List[ChunkPayload] = []
            global_index = 0
            for page in pages:
                page_text = page.text.strip()
                if not page_text:
                    continue
                p_chunks = self._chunk_single_text(
                    text=page_text,
                    page_number=page.page_number,
                    start_index=global_index
                )
                all_chunks.extend(p_chunks)
                global_index += len(p_chunks)
            return all_chunks

        # Single block or fallback text chunking
        cleaned_text = text.strip()
        if not cleaned_text:
            return []

        return self._chunk_single_text(
            text=cleaned_text,
            page_number=page_number,
            start_index=0
        )

    def _chunk_single_text(
        self,
        text: str,
        page_number: Optional[int],
        start_index: int
    ) -> List[ChunkPayload]:
        """
        Chunks a single contiguous text string using sliding window and word boundary snapping.
        """
        if not text:
            return []

        text_length = len(text)
        # Short text optimization: single chunk if text fits within chunk_size
        if text_length <= self.chunk_size:
            return [
                ChunkPayload(
                    content=text,
                    chunk_index=start_index,
                    page_number=page_number
                )
            ]

        chunks: List[ChunkPayload] = []
        current_idx = start_index
        start = 0

        while start < text_length:
            end = start + self.chunk_size

            if end >= text_length:
                chunk_str = text[start:].strip()
                if chunk_str:
                    chunks.append(
                        ChunkPayload(
                            content=chunk_str,
                            chunk_index=current_idx,
                            page_number=page_number
                        )
                    )
                break

            # Snap end boundary to nearest preceding space/newline to avoid cutting words
            break_pos = end
            space_found = False
            lookback_limit = max(start + 1, end - min(self.chunk_overlap, 100))
            for i in range(end, lookback_limit - 1, -1):
                if text[i] in (" ", "\n", "\t"):
                    break_pos = i
                    space_found = True
                    break

            if not space_found:
                break_pos = end

            chunk_str = text[start:break_pos].strip()
            if chunk_str:
                chunks.append(
                    ChunkPayload(
                        content=chunk_str,
                        chunk_index=current_idx,
                        page_number=page_number
                    )
                )
                current_idx += 1

            # Advance start index considering overlap
            advance = max(1, (break_pos - start) - self.chunk_overlap)
            start += advance

        return chunks


def get_text_chunker(
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> BaseTextChunker:
    """
    Factory function returning active TextChunker instance with optional config overrides.
    """
    return TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
