"""
Domain Exceptions Module

Defines application-specific domain exceptions.
Decouples core business logic and repository layers from HTTP/Web framework concerns.
"""

class AppException(Exception):
    """
    Base domain exception for the application.
    All custom domain errors inherit from this class.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UserAlreadyExistsError(AppException):
    """Raised when attempting to register an email address that is already registered."""
    pass


class InvalidCredentialsError(AppException):
    """Raised when authentication credentials (email/password or token) fail verification."""
    pass


class UserNotFoundError(AppException):
    """Raised when a user record cannot be found by ID or email."""
    pass


class DocumentNotFoundError(AppException):
    """Raised when a document record cannot be found or is not accessible to the current user."""
    pass


class DocumentAccessDeniedError(AppException):
    """Raised when a user attempts to access or modify a document owned by another user."""
    pass


class DocumentAlreadyProcessingError(AppException):
    """Raised when a document is currently undergoing background processing."""
    pass


class DocumentProcessingError(AppException):
    """Raised when an internal error occurs during OCR, LLM extraction, chunking, or embedding generation."""
    pass


class StorageOperationError(AppException):
    """Raised when an external storage operation (upload URL, download URL, file read/delete) fails."""
    pass


class ValidationError(AppException):
    """Raised when business input validation fails."""
    pass
