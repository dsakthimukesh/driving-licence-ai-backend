"""
Embedding Service Module

Provides function-based business logic for batch generating dense vector embeddings
and storing vectors in `public.document_chunks`.
"""

import uuid
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.document_chunk import DocumentChunk
from app.repositories import document_chunk_repository
from app.services.embeddings import get_embedding_provider


async def generate_and_store_embeddings(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> int:
    """
    Generates 1536-dimensional dense vector embeddings for all document chunks missing vectors.

    1. Queries document chunks from repository for target document.
    2. Filters chunks needing embeddings.
    3. Calls Gemini Embedding Provider batch embedding interface.
    4. Updates database records with vector array payload.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Target document UUID.

    Returns:
        Total number of chunk embeddings updated.
    """
    chunks = document_chunk_repository.get_chunks_by_document_id(db=db, document_id=document_id)
    if not chunks:
        return 0

    unembedded_chunks = [c for c in chunks if c.embedding is None]
    if not unembedded_chunks:
        return 0

    texts = [c.content for c in unembedded_chunks]

    provider = get_embedding_provider()
    embeddings: List[List[float]] = await provider.generate_embeddings(texts=texts)

    for chunk, emb in zip(unembedded_chunks, embeddings):
        document_chunk_repository.update_chunk_embedding(
            db=db,
            chunk_id=chunk.document_chunk_id,
            embedding=emb
        )

    return len(embeddings)


async def reembed_all_document_chunks(db: Session) -> int:
    """
    Re-embeds all document chunks in `public.document_chunks` using Google Gemini embedding model.
    Overwrites existing (OpenAI or synthetic) vector embeddings with verified Gemini embeddings.
    """
    stmt = select(DocumentChunk).order_by(DocumentChunk.chunk_index.asc())
    all_chunks = list(db.execute(stmt).scalars().all())

    if not all_chunks:
        return 0

    texts = [c.content for c in all_chunks]
    provider = get_embedding_provider()
    embeddings: List[List[float]] = await provider.generate_embeddings(texts=texts)

    for chunk, emb in zip(all_chunks, embeddings):
        document_chunk_repository.update_chunk_embedding(
            db=db,
            chunk_id=chunk.document_chunk_id,
            embedding=emb
        )

    return len(embeddings)
