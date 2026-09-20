"""
User Repository Module

Provides database access functions for the `public.users` table using SQLAlchemy 2.x.
Contains purely data persistence and retrieval queries without business logic or HTTP exceptions.
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """
    Fetch a single user by their unique primary key identifier.

    Args:
        db: Active SQLAlchemy database session.
        user_id: Unique UUID identifier of the target user.

    Returns:
        The matching User ORM model instance if found, or None if not found.
    """
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Fetch a user record using their normalized email address.

    Args:
        db: Active SQLAlchemy database session.
        email: Lowercase normalized email string to search for.

    Returns:
        The matching User ORM model instance if found, or None if not found.
    """
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.email == normalized_email)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, user: User) -> User:
    """
    Persists a new User record into the database.

    Args:
        db: Active SQLAlchemy database session.
        user: Instantiated User ORM model instance to persist.

    Returns:
        The created User ORM instance refreshed with database state.

    Raises:
        Database errors (SQLAlchemy / DBAPI exceptions) on constraint violations.
    """
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e
