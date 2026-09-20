import uuid
from typing import List
from pydantic import BaseModel, Field


class OCRPageResult(BaseModel):
    """
    Extracted text result for a single page inside a document.
    """
    page_number: int = Field(
        ...,
        ge=1,
        description="1-based page index."
    )
    text: str = Field(
        ...,
        description="Extracted OCR raw text for this page."
    )


class OCRResult(BaseModel):
    """
    Structured response model containing complete OCR text extraction output.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    provider: str = Field(
        ...,
        description="Name of the OCR provider engine used (e.g. 'aws_textract', 'local_pypdf')."
    )
    text: str = Field(
        ...,
        description="Combined raw extracted OCR text across all document pages."
    )
    pages: List[OCRPageResult] = Field(
        default_factory=list,
        description="Per-page extracted text breakdown."
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total OCR execution time in milliseconds."
    )
