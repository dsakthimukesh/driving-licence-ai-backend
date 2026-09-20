import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """
    Request payload schema for user registration.
    Includes validation rules for name, email format, and password strength.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the registering user."
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address for login identity."
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (minimum 8 characters)."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or blank.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.strip().lower()


class UserRegisterResponse(BaseModel):
    """
    Response payload schema for successful user registration.
    Excludes sensitive fields like password or hashed_password.
    """
    user_id: uuid.UUID = Field(
        ...,
        description="Generated unique user identifier (UUID)."
    )
    name: str = Field(
        ...,
        description="Full name of the registered user."
    )
    email: str = Field(
        ...,
        description="Registered email address."
    )
    message: str = Field(
        default="User registered successfully",
        description="Status message indicating successful creation."
    )

    model_config = {
        "from_attributes": True
    }


class UserLoginRequest(BaseModel):
    """
    Request payload schema for user authentication.
    """
    email: EmailStr = Field(
        ...,
        description="Registered user email address."
    )
    password: str = Field(
        ...,
        description="User plain-text password."
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.strip().lower()


class UserInfo(BaseModel):
    """
    Safe nested user detail model inside login response.
    """
    user_id: uuid.UUID = Field(
        ...,
        description="User unique identifier (UUID)."
    )
    name: str = Field(
        ...,
        description="Full name of the user."
    )
    email: str = Field(
        ...,
        description="Email address of the user."
    )

    model_config = {
        "from_attributes": True
    }


class UserLoginResponse(BaseModel):
    """
    Response payload schema for successful user authentication containing JWT.
    """
    access_token: str = Field(
        ...,
        description="Signed JWT access token."
    )
    token_type: str = Field(
        default="bearer",
        description="Token authorization type."
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds."
    )
    user: UserInfo = Field(
        ...,
        description="Sanitized user profile information."
    )


class UserMeResponse(BaseModel):
    """
    Response payload schema for GET /me authenticated profile request.
    """
    user_id: uuid.UUID = Field(
        ...,
        description="User unique identifier (UUID)."
    )
    name: str = Field(
        ...,
        description="Full name of the authenticated user."
    )
    email: str = Field(
        ...,
        description="Email address of the authenticated user."
    )

    model_config = {
        "from_attributes": True
    }
