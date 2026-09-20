"""
Document Info Repository Module

Provides database access functions for the `public.document_info` table using SQLAlchemy 2.x.
Stores and queries structured driving licence metadata extracted by LLM.
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.models.document_info import DocumentInfo


def get_document_info_by_document_id(
    db: Session,
    document_id: uuid.UUID
) -> Optional[DocumentInfo]:
    """
    Fetch extracted driving licence information for a specific document.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Unique UUID identifier of the document.

    Returns:
        Matching DocumentInfo model instance or None if not present.
    """
    stmt = select(DocumentInfo).where(DocumentInfo.document_id == document_id)
    return db.execute(stmt).scalar_one_or_none()


def upsert_document_info(
    db: Session,
    document_info: DocumentInfo
) -> DocumentInfo:
    """
    Inserts or updates structured document info record in public.document_info.

    Args:
        db: Active SQLAlchemy database session.
        document_info: DocumentInfo model instance to save.

    Returns:
        Refreshed DocumentInfo model instance.
    """
    try:
        db.add(document_info)
        db.commit()
        db.refresh(document_info)
        return document_info
    except Exception as e:
        db.rollback()
        raise e


def delete_document_info_by_document_id(
    db: Session,
    document_id: uuid.UUID
) -> int:
    """
    Deletes structured document info record associated with a document ID.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Target document UUID.

    Returns:
        Number of deleted rows.
    """
    try:
        result = db.execute(
            text("DELETE FROM public.document_info WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        db.commit()
        return result.rowcount
    except Exception as e:
        db.rollback()
        raise e
