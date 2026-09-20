from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.ocr.models import OCRPageResult


class ChunkPayload(BaseModel):
    """
    Payload data structure for a single extracted text chunk.
    """
    content: str = Field(
        ...,
        min_length=1,
        description="Cleaned text content of the chunk."
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="0-based index reflecting chronological position of chunk in document."
    )
    page_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="1-based page index from source document if available."
    )


class BaseTextCleaner(ABC):
    """
    Abstract Base Class for text cleaning engines.
    """

    @abstractmethod
    def clean_text(self, text: Optional[str]) -> str:
        """
        Cleans and normalizes raw OCR text safely without LLM calls.
        """
        pass


class BaseTextChunker(ABC):
    """
    Abstract Base Class for text chunking strategies.
    """

    @abstractmethod
    def split_into_chunks(
        self,
        text: str,
        page_number: Optional[int] = None,
        pages: Optional[List[OCRPageResult]] = None
    ) -> List[ChunkPayload]:
        """
        Splits cleaned text into structured overlapping ChunkPayload objects.
        """
        pass
