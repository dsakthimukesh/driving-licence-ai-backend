import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.core.database import Base


class VectorType(UserDefinedType):
    """
    SQLAlchemy UserDefinedType mapping PostgreSQL pgvector VECTOR(1536) type.
    Handles automatic serialization between List[float] and PostgreSQL vector string representation ('[0.1, 0.2, ...]').
    """
    def get_col_spec(self, **kw) -> str:
        return "VECTOR(1536)"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return "[" + ",".join(str(float(x)) for x in value) + "]"
            return str(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                clean = value.strip("[] \t\n\r")
                if not clean:
                    return []
                return [float(x) for x in clean.split(",") if x.strip()]
            return value
        return process


class DocumentChunk(Base):
    """
    SQLAlchemy 2.x ORM Model mapping the existing `public.document_chunks` PostgreSQL table.
    
    Stores text chunks generated from document OCR output along with chunk index, page metadata,
    and audit fields for vector embeddings and RAG operations.
    """
    __tablename__ = "document_chunks"
    __table_args__ = {"schema": "public"}

    # document_chunk_id: Unique UUID Primary Key.
    document_chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier (UUID) for the document chunk."
    )

    # document_id: Foreign key referencing public.documents.document_id.
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.documents.document_id"),
        nullable=False,
        index=True,
        comment="Foreign key referencing parent document."
    )

    # chunk_index: 0-based sequential order index of the chunk.
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="0-based sequential order index of the chunk."
    )

    # content: Cleaned text content of the chunk.
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cleaned OCR text chunk content."
    )

    # page_number: Optional 1-based source page number.
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="1-based page number (nullable if page breakdown unavailable)."
    )

    # embedding: Vector(1536) column for text embeddings (populated in future RAG stage).
    embedding: Mapped[Optional[Any]] = mapped_column(
        VectorType(),
        nullable=True,
        comment="1536-dimensional float vector embedding."
    )

    # created_by: UUID reference to user who created the chunk.
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of account that created the chunk record."
    )

    # created_date: Timezone-aware creation timestamp.
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp with time zone (TIMESTAMPTZ)."
    )

    # last_modified_by: UUID reference to user who last updated the chunk.
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of account that last modified the chunk record."
    )

    # last_modified_date: Timezone-aware modification timestamp.
    last_modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last modification timestamp with time zone (TIMESTAMPTZ)."
    )
