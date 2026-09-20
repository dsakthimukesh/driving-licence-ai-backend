"""
Core Dependencies Module

Provides FastAPI dependency functions for database sessions and authentication.
"""

import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import get_user_by_id

# HTTP Bearer security scheme for Swagger UI & Authorization header parsing
security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract, decode, and validate the JWT Bearer token from HTTP headers.

    Args:
        credentials: Authorization header Bearer token credentials.
        db: Active SQLAlchemy database session injected via FastAPI.

    Returns:
        The authenticated User ORM model instance.

    Raises:
        HTTPException 401 Unauthorized if the token is missing, invalid, expired, or user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Query user from repository layer
    user = get_user_by_id(db=db, user_id=user_id)

    if user is None:
        raise credentials_exception

    return user
