"""
Auth Controller Module

Handles HTTP-level request orchestration for user registration, authentication, and profile fetching.
Translates domain-level exceptions into standardized HTTP error responses.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AppException
)
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserMeResponse
)
from app.services import auth_service


def handle_register_user(db: Session, request: UserRegisterRequest) -> UserRegisterResponse:
    """
    Controller function handling user registration HTTP endpoint.

    Args:
        db: Active SQLAlchemy database session.
        request: Validated UserRegisterRequest model.

    Returns:
        UserRegisterResponse payload.

    Raises:
        HTTPException 409 Conflict if email is already registered.
        HTTPException 500 Internal Server Error for unexpected domain errors.
    """
    try:
        new_user = auth_service.register_user(db=db, request=request)
        return UserRegisterResponse(
            user_id=new_user.user_id,
            name=new_user.name,
            email=new_user.email,
            message="User registered successfully"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration."
        ) from e


def handle_login_user(db: Session, request: UserLoginRequest) -> UserLoginResponse:
    """
    Controller function handling user login HTTP endpoint.

    Args:
        db: Active SQLAlchemy database session.
        request: Validated UserLoginRequest model.

    Returns:
        UserLoginResponse payload with JWT access token.

    Raises:
        HTTPException 401 Unauthorized if authentication fails.
    """
    try:
        return auth_service.login_user(db=db, request=request)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login."
        ) from e


def handle_get_me(current_user: User) -> UserMeResponse:
    """
    Controller function handling authenticated user profile HTTP endpoint.

    Args:
        current_user: Authenticated User model.

    Returns:
        UserMeResponse profile payload.
    """
    return UserMeResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email
    )
