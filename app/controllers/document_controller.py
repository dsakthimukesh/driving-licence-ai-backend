"""
Document Controller Module

Handles HTTP-level request orchestration for document management and processing endpoints.
Translates domain exceptions into standard HTTP status codes.
"""

import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyProcessingError,
    DocumentProcessingError,
    StorageOperationError,
    ValidationError,
    AppException
)
from app.models.user import User
from app.schemas.document import (
    DocumentUploadUrlRequest,
    DocumentUploadUrlResponse,
    DocumentConfirmUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentDownloadUrlResponse,
    DocumentInfoResponse,
    DocumentInfoUpdateRequest
)
from app.services import document_service, document_processing_service
from app.services.ocr import OCRResult


def handle_generate_upload_url(
    db: Session,
    current_user: User,
    request: DocumentUploadUrlRequest
) -> DocumentUploadUrlResponse:
    """Controller function for generating a pre-signed storage upload URL."""
    try:
        return document_service.initialize_upload(
            db=db,
            current_user=current_user,
            request=request
        )
    except StorageOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_confirm_upload(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentConfirmUploadResponse:
    """Controller function for confirming document storage upload."""
    try:
        return document_service.confirm_upload(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def handle_process_document(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> OCRResult:
    """Controller function for triggering async document intelligence pipeline."""
    try:
        return await document_processing_service.process_document(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DocumentAlreadyProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_list_documents(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None
) -> DocumentListResponse:
    """Controller function for listing user documents with pagination."""
    try:
        return document_service.list_user_documents(
            db=db,
            current_user=current_user,
            page=page,
            page_size=page_size,
            status_filter=status_filter
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_get_document_details(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentDetailResponse:
    """Controller function for fetching detailed metadata for a single document."""
    try:
        return document_service.get_user_document(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_generate_download_url(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentDownloadUrlResponse:
    """Controller function for generating a temporary signed download URL."""
    try:
        return document_service.generate_download_url(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except StorageOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_delete_document(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> None:
    """Controller function for deleting a document and related resources."""
    try:
        document_service.delete_user_document(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_get_document_info(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentInfoResponse:
    """Controller function for fetching extracted driving licence information."""
    try:
        return document_processing_service.get_document_info(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def handle_update_document_info(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    request: DocumentInfoUpdateRequest
) -> DocumentInfoResponse:
    """Controller function for updating extracted driving licence information."""
    try:
        return document_processing_service.update_document_info(
            db=db,
            current_user=current_user,
            document_id=document_id,
            request=request
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

