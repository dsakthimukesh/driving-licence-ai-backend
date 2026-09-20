"""
Auth Service Module

Provides function-based business logic for user registration and JWT authentication.
Decouples repository data access and security utilities from HTTP controllers.
"""

import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserLoginResponse,
    UserInfo
)
from app.utils.datetime_utils import get_utc_now


def register_user(db: Session, request: UserRegisterRequest) -> User:
    """
    Registers a new user into the system.

    1. Normalizes input email and queries database repository to check for existing accounts.
    2. Raises UserAlreadyExistsError if email is already registered.
    3. Hashes password securely using Argon2id.
    4. Generates UUID primary key and constructs User ORM model.
    5. Persists model using repository layer.

    Args:
        db: Active SQLAlchemy database session.
        request: Validated UserRegisterRequest Pydantic model containing name, email, and password.

    Returns:
        The created User ORM model instance.

    Raises:
        UserAlreadyExistsError: If input email is already in use.
    """
    normalized_email = request.email.strip().lower()

    # Check for existing email in repository
    existing_user = user_repository.get_user_by_email(db=db, email=normalized_email)
    if existing_user is not None:
        raise UserAlreadyExistsError("Email is already registered")

    # Hash password with Argon2
    hashed_pwd = hash_password(request.password)

    new_user_id = uuid.uuid4()
    now_utc = get_utc_now()

    new_user = User(
        user_id=new_user_id,
        name=request.name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        created_by=new_user_id,
        created_date=now_utc,
        last_modified_by=new_user_id,
        last_modified_date=now_utc
    )

    return user_repository.create_user(db=db, user=new_user)


def login_user(db: Session, request: UserLoginRequest) -> UserLoginResponse:
    """
    Authenticates user credentials and issues a signed JWT access token.

    1. Normalizes input email and queries repository for matching User record.
    2. Verifies provided plaintext password against stored Argon2 password hash.
    3. Raises InvalidCredentialsError if email or password fail verification.
    4. Encodes user_id into JWT access token with configured expiration payload.

    Args:
        db: Active SQLAlchemy database session.
        request: Validated UserLoginRequest Pydantic model with email and password.

    Returns:
        UserLoginResponse Pydantic model containing access token string and user profile info.

    Raises:
        InvalidCredentialsError: If credentials fail verification.
    """
    normalized_email = request.email.strip().lower()

    user = user_repository.get_user_by_email(db=db, email=normalized_email)
    if user is None or not verify_password(request.password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")

    # Generate JWT access token with user_id as 'sub' claim
    access_token = create_access_token(data={"sub": str(user.user_id)})
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserInfo(
            user_id=user.user_id,
            name=user.name,
            email=user.email
        )
    )


class AuthService:
    """Backward-compatible class wrapper around auth_service functions."""

    @classmethod
    def register_user(cls, db: Session, request: UserRegisterRequest) -> User:
        return register_user(db=db, request=request)

    @classmethod
    def login_user(cls, db: Session, request: UserLoginRequest) -> UserLoginResponse:
        return login_user(db=db, request=request)

