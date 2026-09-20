"""
Chunking Service Module

Provides function-based business logic for cleaning raw OCR text, creating overlapping text chunks,
and persisting chunk records into `public.document_chunks`.
"""

import uuid
from typing import List
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.repositories import document_chunk_repository
from app.services.chunking import get_text_cleaner, get_text_chunker, ChunkPayload
from app.utils.datetime_utils import get_utc_now


def process_and_save_chunks(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    raw_ocr_text: str,
    pages_data: list = None
) -> List[DocumentChunk]:
    """
    Cleans raw OCR text, splits text into overlapping chunks, and persists them to the database.

    1. Uses TextCleaner utility to strip noise and normalize whitespace.
    2. Uses TextChunker to divide text into sliding window chunks with page numbers.
    3. Builds DocumentChunk ORM models.
    4. Persists chunks using `document_chunk_repository`.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Unique UUID of document being processed.
        raw_ocr_text: Raw text output from OCR stage.
        pages_data: Optional list of Page OCR structures.

    Returns:
        List of saved DocumentChunk ORM model instances.
    """
    # Delete pre-existing chunks for idempotency
    document_chunk_repository.delete_chunks_by_document_id(db=db, document_id=document_id)

    # 1. Clean raw OCR text
    cleaner = get_text_cleaner()
    cleaned_text = cleaner.clean_text(raw_ocr_text)

    # 2. Split into chunks
    chunker = get_text_chunker()
    chunks: List[ChunkPayload] = chunker.split_into_chunks(
        text=cleaned_text,
        pages=pages_data
    )

    # 3. Construct ORM models
    now_utc = get_utc_now()
    chunk_models: List[DocumentChunk] = []

    for c in chunks:
        chunk_model = DocumentChunk(
            document_chunk_id=uuid.uuid4(),
            document_id=document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            embedding=None,  # Embeddings populated in subsequent pipeline step
            created_by=current_user.user_id,
            created_date=now_utc,
            last_modified_by=current_user.user_id,
            last_modified_date=now_utc
        )
        chunk_models.append(chunk_model)

    # 4. Save to repository
    return document_chunk_repository.save_chunks(db=db, chunks=chunk_models)
