import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    SQLAlchemy 2.x ORM Model mapping the existing `public.users` PostgreSQL table.
    
    This model supports custom authentication with user credentials stored directly in
    the `public.users` table instead of relying on Supabase Auth (`auth.users`).
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    # user_id: Unique UUID Primary Key.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier (UUID) for the user."
    )

    # name: Required user full name up to 100 characters.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full name of the user."
    )

    # email: Unique required email address up to 255 characters, indexed for fast lookup.
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address used as login identity."
    )

    # hashed_password: Required text field containing the securely hashed user password.
    hashed_password: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Bcrypt/Argon2 hashed representation of the user password."
    )

    # created_by: Optional UUID reference to the admin/system user who created this account.
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the creator account (nullable)."
    )

    # created_date: Required timezone-aware timestamp when the record was created.
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp with time zone (TIMESTAMPTZ)."
    )

    # last_modified_by: Optional UUID reference to the user who last modified this record.
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the last modifier account (nullable)."
    )

    # last_modified_date: Required timezone-aware timestamp when the record was last updated.
    last_modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last modification timestamp with time zone (TIMESTAMPTZ)."
    )
