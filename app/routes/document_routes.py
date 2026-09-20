"""
Document Routes Module

Defines HTTP routes for document management (upload, list, details, download, delete) and processing (OCR, LLM info).
Delegates execution to `app.controllers.document_controller`.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
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
from app.controllers import document_controller
from app.services.ocr import OCRResult

router = APIRouter()


@router.post(
    "/upload-url",
    response_model=DocumentUploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate pre-signed upload URL",
    description="Generates a temporary pre-signed upload URL for direct storage upload."
)
def generate_upload_url(
    request: DocumentUploadUrlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initializes document upload. Delegates to document_controller.handle_generate_upload_url."""
    return document_controller.handle_generate_upload_url(
        db=db, current_user=current_user, request=request
    )


@router.post(
    "/{document_id}/confirm-upload",
    response_model=DocumentConfirmUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm document upload in storage",
    description="Verifies that the uploaded file exists at storage_path in Supabase Storage."
)
def confirm_upload(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirms file upload in storage. Delegates to document_controller.handle_confirm_upload."""
    return document_controller.handle_confirm_upload(
        db=db, current_user=current_user, document_id=document_id
    )


@router.post(
    "/{document_id}/process",
    response_model=OCRResult,
    status_code=status.HTTP_200_OK,
    summary="Process document through OCR & AI pipeline",
    description="Triggers OCR text extraction, LLM structured extraction, text chunking, and embedding generation."
)
async def process_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers end-to-end document processing. Delegates to document_controller.handle_process_document."""
    return await document_controller.handle_process_document(
        db=db, current_user=current_user, document_id=document_id
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's documents",
    description="Returns a paginated list of documents owned by the authenticated user with optional status filter."
)
def list_documents(
    page: int = Query(default=1, ge=1, description="Page number (1-based index)."),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size limit (1 to 100)."),
    status: Optional[str] = Query(default=None, description="Optional status filter."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists user documents. Delegates to document_controller.handle_list_documents."""
    return document_controller.handle_list_documents(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description="Fetches detailed metadata for a document owned by the authenticated user."
)
def get_document_details(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches document details. Delegates to document_controller.handle_get_document_details."""
    return document_controller.handle_get_document_details(
        db=db, current_user=current_user, document_id=document_id
    )


@router.get(
    "/{document_id}/download-url",
    response_model=DocumentDownloadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate signed download URL",
    description="Generates a temporary pre-signed download URL for a document (5-minute expiration)."
)
def generate_download_url(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates pre-signed download URL. Delegates to document_controller.handle_generate_download_url."""
    return document_controller.handle_generate_download_url(
        db=db, current_user=current_user, document_id=document_id
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Deletes a document owned by user, removing storage file and database record."
)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes document. Delegates to document_controller.handle_delete_document."""
    document_controller.handle_delete_document(
        db=db, current_user=current_user, document_id=document_id
    )
    return None


@router.get(
    "/{document_id}/info",
    response_model=DocumentInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get structured document information",
    description="Fetches LLM-extracted driving licence information for a document."
)
def get_document_info(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches structured licence info. Delegates to document_controller.handle_get_document_info."""
    return document_controller.handle_get_document_info(
        db=db, current_user=current_user, document_id=document_id
    )


@router.put(
    "/{document_id}/info",
    response_model=DocumentInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update extracted document information",
    description="Updates extracted driving licence fields for a document owned by the authenticated user."
)
def update_document_info(
    document_id: uuid.UUID,
    request: DocumentInfoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates structured licence info. Delegates to document_controller.handle_update_document_info."""
    return document_controller.handle_update_document_info(
        db=db, current_user=current_user, document_id=document_id, request=request
    )

