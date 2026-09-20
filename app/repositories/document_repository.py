"""
Document Repository Module

Provides database access functions for the `public.documents` table using SQLAlchemy 2.x.
Handles CRUD queries, ownership-scoped filters, paginated listing, and status updates.
"""

import math
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from app.models.document import Document


def create_document(db: Session, document: Document) -> Document:
    """
    Persists a new document metadata record into the database.

    Args:
        db: Active SQLAlchemy database session.
        document: Instantiated Document ORM model instance.

    Returns:
        The created Document instance refreshed from database.
    """
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except Exception as e:
        db.rollback()
        raise e


def get_document_by_id(db: Session, document_id: uuid.UUID) -> Optional[Document]:
    """
    Fetch a single document record by its primary key UUID.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Unique UUID identifier of the document.

    Returns:
        Matching Document model instance or None if not found.
    """
    stmt = select(Document).where(Document.document_id == document_id)
    return db.execute(stmt).scalar_one_or_none()


def get_user_document_by_id(
    db: Session,
    document_id: uuid.UUID,
    user_id: uuid.UUID
) -> Optional[Document]:
    """
    Fetch a document record ensuring it belongs to a specific user.

    Args:
        db: Active SQLAlchemy database session.
        document_id: Unique UUID identifier of the document.
        user_id: UUID of the owning user.

    Returns:
        Matching Document instance if owned by user, otherwise None.
    """
    stmt = (
        select(Document)
        .where(Document.document_id == document_id)
        .where(Document.user_id == user_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_user_documents(
    db: Session,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None
) -> Tuple[List[Document], int, int]:
    """
    Fetches a paginated list of documents owned by a user with optional status filter.

    Args:
        db: Active SQLAlchemy database session.
        user_id: Owner user UUID.
        page: Page number (1-based index).
        page_size: Maximum items per page.
        status_filter: Optional status string (PENDING, PROCESSING, COMPLETED, FAILED).

    Returns:
        Tuple containing:
            - List of matching Document ORM records.
            - Total matching item count.
            - Total page count.
    """
    base_stmt = select(Document).where(Document.user_id == user_id)

    if status_filter:
        base_stmt = base_stmt.where(Document.status == status_filter.upper())

    # Count total matching items using subquery
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_items = db.execute(count_stmt).scalar_one()

    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    # Paginated statement sorted by created_date DESC
    paginated_stmt = (
        base_stmt
        .order_by(Document.created_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    documents = db.execute(paginated_stmt).scalars().all()

    return list(documents), total_items, total_pages


def update_document_status(
    db: Session,
    document: Document,
    new_status: str,
    last_modified_by: uuid.UUID
) -> Document:
    """
    Updates the lifecycle status of a document record.

    Args:
        db: Active SQLAlchemy database session.
        document: Document ORM instance to update.
        new_status: Target status string (PENDING, PROCESSING, COMPLETED, FAILED).
        last_modified_by: User UUID making the update.

    Returns:
        Refreshed Document ORM instance.
    """
    from datetime import datetime, timezone

    document.status = new_status
    document.last_modified_by = last_modified_by
    document.last_modified_date = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(document)
        return document
    except Exception as e:
        db.rollback()
        raise e


def delete_document(db: Session, document: Document) -> None:
    """
    Deletes a Document record from the database.

    Args:
        db: Active SQLAlchemy database session.
        document: Document ORM instance to delete.
    """
    try:
        db.delete(document)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
