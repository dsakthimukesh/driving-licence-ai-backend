import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):
    """
    SQLAlchemy 2.x ORM Model mapping the existing `public.documents` PostgreSQL table.
    
    Tracks uploaded driving licence files, storage paths, ownership, and workflow status.
    """
    __tablename__ = "documents"
    __table_args__ = {"schema": "public"}

    # document_id: Unique UUID Primary Key.
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier (UUID) for the document."
    )

    # user_id: Foreign key referencing public.users.user_id.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.user_id"),
        nullable=False,
        index=True,
        comment="Foreign key referencing the owner user account."
    )

    # file_name: Original or normalized filename up to 255 characters.
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the file as submitted by the user."
    )

    # bucket_name: Supabase Storage bucket name (e.g. 'documents').
    bucket_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Supabase Storage bucket name."
    )

    # storage_path: Relative object path inside Supabase Storage.
    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Unique object storage path inside Supabase Storage bucket."
    )

    # status: Document processing status (PENDING, PROCESSING, COMPLETED, FAILED).
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        comment="Workflow processing status."
    )

    # created_by: UUID reference to the user who uploaded the document.
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the user who created the document record."
    )

    # created_date: Timezone-aware creation timestamp.
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when document record was created (TIMESTAMPTZ)."
    )

    # last_modified_by: UUID reference to the user who last modified the document record.
    last_modified_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the user who last modified the record."
    )

    # last_modified_date: Timezone-aware modification timestamp.
    last_modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Timestamp when document record was last updated (TIMESTAMPTZ)."
    )
