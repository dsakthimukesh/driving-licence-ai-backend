"""
Document Chunk Repository Module

Provides database access functions for the `public.document_chunks` table using SQLAlchemy 2.x and pgvector.
Manages chunk persistence, batch vector embedding updates, and cosine similarity vector retrieval.
"""

import uuid
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.models.document_chunk import DocumentChunk


def save_chunks(
    db: Session,
    chunks: List[DocumentChunk]
) -> List[DocumentChunk]:
    """
    Bulk saves document chunk ORM records into public.document_chunks.

    Args:
        db: Active SQLAlchemy database session.
        chunks: List of DocumentChunk model instances to persist.

    Returns:
        List of saved DocumentChunk instances.
    """
    try:
        db.add_all(chunks)
        db.commit()
        for chunk in chunks:
            db.refresh(chunk)
        return chunks
    except Exception as e:
        db.rollback()
        raise e


def get_chunks_by_document_id(
    db: Session,
    document_id: uuid.UUID
) -> List[DocumentChunk]:
    """
    Fetches all text chunks associated with a document ordered by chunk_index ASC.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Target document UUID.

    Returns:
        List of DocumentChunk model records.
    """
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(db.execute(stmt).scalars().all())


def update_chunk_embedding(
    db: Session,
    chunk_id: uuid.UUID,
    embedding: List[float]
) -> None:
    """
    Updates vector embedding column for a specific chunk.

    Args:
        db: Active SQLAlchemy database session.
        chunk_id: Document chunk UUID.
        embedding: List of 1536 float values.
    """
    try:
        stmt = select(DocumentChunk).where(DocumentChunk.document_chunk_id == chunk_id)
        chunk = db.execute(stmt).scalar_one_or_none()
        if chunk:
            chunk.embedding = embedding
            db.commit()
    except Exception as e:
        db.rollback()
        raise e


def get_similar_chunks(
    db: Session,
    document_id: uuid.UUID,
    query_embedding: List[float],
    top_k: int = 3
) -> List[Tuple[DocumentChunk, float]]:
    """
    Executes PostgreSQL pgvector cosine distance similarity query to find most relevant chunks.

    Calculates cosine similarity as `1 - cosine_distance`.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Unique UUID identifier of target document.
        query_embedding: Dense vector embedding array of query text (1536 floats).
        top_k: Maximum number of top matches to return.

    Returns:
        List of tuples: (DocumentChunk model, similarity_score float).
    """
    q_vec_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
    query_sql = text("""
        SELECT document_chunk_id, document_id, chunk_index, content, page_number,
               1.0 - (embedding <=> CAST(:q_vec AS vector)) AS similarity_score
        FROM public.document_chunks
        WHERE document_id = :document_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:q_vec AS vector) ASC
        LIMIT :top_k
    """)
    rows = db.execute(
        query_sql,
        {
            "document_id": str(document_id),
            "q_vec": q_vec_str,
            "top_k": top_k
        }
    ).mappings().all()

    output = []
    for row in rows:
        chunk = DocumentChunk(
            document_chunk_id=uuid.UUID(str(row["document_chunk_id"])),
            document_id=uuid.UUID(str(row["document_id"])),
            chunk_index=int(row["chunk_index"]),
            content=str(row["content"]),
            page_number=int(row["page_number"]) if row["page_number"] is not None else None
        )
        score = float(row["similarity_score"])
        output.append((chunk, score))
    return output


def delete_chunks_by_document_id(
    db: Session,
    document_id: uuid.UUID
) -> int:
    """
    Deletes all chunk records associated with a document ID.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Target document UUID.

    Returns:
        Number of deleted rows.
    """
    try:
        result = db.execute(
            text("DELETE FROM public.document_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        db.commit()
        return result.rowcount
    except Exception as e:
        db.rollback()
        raise e
