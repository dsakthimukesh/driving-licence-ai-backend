import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentInfo(Base):
    """
    SQLAlchemy 2.x ORM Model mapping the existing `public.document_info` PostgreSQL table.
    
    Stores structured driving licence fields extracted via LLM processing.
    """
    __tablename__ = "document_info"
    __table_args__ = {"schema": "public"}

    # document_info_id: Primary Key UUID.
    document_info_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier (UUID) for the document info record."
    )

    # document_id: Foreign Key referencing public.documents.document_id.
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.documents.document_id"),
        nullable=False,
        unique=True,
        index=True,
        comment="Foreign key referencing the associated document."
    )

    licence_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Extracted driving licence number (e.g. DL-1420110012345)."
    )

    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Full name of the licence holder."
    )

    parent_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Father's/Mother's/Spouse's name."
    )

    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of birth of the licence holder."
    )

    blood_group: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Blood group (e.g. O+, A+, B+, or verbose extracted blood group descriptions)."
    )

    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full address listed on the licence."
    )

    issue_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of issue of the licence."
    )

    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expiry date of the licence."
    )

    vehicle_authorization: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Classes of vehicles authorized to drive (e.g. LMV, MCWG)."
    )

    issuing_authority: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Name or location of the issuing RTO authority."
    )

    restrictions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Specific licence restrictions or endorsements."
    )

    other_information: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Uncertain text, remarks, or extra extracted details."
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the user who created the record."
    )

    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp (TIMESTAMPTZ)."
    )

    last_modified_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email address of the user who last modified the record."
    )

    last_modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last modification timestamp (TIMESTAMPTZ)."
    )
