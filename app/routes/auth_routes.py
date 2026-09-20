"""
Auth Routes Module

Defines HTTP routes for user registration, authentication, and current profile fetching.
Delegates execution to `app.controllers.auth_controller`.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserMeResponse
)
from app.controllers import auth_controller

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user account into the system using Argon2 password hashing."
)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user. Delegates to auth_controller.handle_register_user.
    """
    return auth_controller.handle_register_user(db=db, request=request)


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token",
    description="Authenticates email and password credentials, returning a signed JWT access token."
)
def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticates user. Delegates to auth_controller.handle_login_user.
    """
    return auth_controller.handle_login_user(db=db, request=request)


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns profile information of the user authenticated via JWT Bearer token."
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Returns profile information of current user. Delegates to auth_controller.handle_get_me.
    """
    return auth_controller.handle_get_me(current_user=current_user)
