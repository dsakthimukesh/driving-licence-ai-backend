"""
Document Service Module

Provides function-based business logic for document initialization, upload confirmation,
paginated listing, detail viewing, pre-signed download URL generation, and deletion.
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    StorageOperationError,
    ValidationError
)
from app.models.document import Document
from app.models.user import User
from app.repositories import (
    document_repository,
    document_info_repository,
    document_chunk_repository
)
from app.schemas.document import (
    ALLOWED_STATUSES,
    DocumentUploadUrlRequest,
    DocumentUploadUrlResponse,
    DocumentConfirmUploadResponse,
    DocumentListItemResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentDownloadUrlResponse
)
from app.services.storage_service import StorageService
from app.utils.file_validation import sanitize_filename
from app.utils.datetime_utils import get_utc_now


def initialize_upload(
    db: Session,
    current_user: User,
    request: DocumentUploadUrlRequest
) -> DocumentUploadUrlResponse:
    """
    Initializes a document upload workflow:

    1. Sanitizes user filename to avoid path traversal.
    2. Generates document UUID and unique storage path key (`user_id/document_id/filename`).
    3. Persists initial Document record with `PENDING` status via `document_repository`.
    4. Generates a temporary pre-signed upload URL using `StorageService`.
    5. If URL generation fails, rolls back DB record to maintain consistency.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User ORM model instance.
        request: Validated DocumentUploadUrlRequest payload containing file_name.

    Returns:
        DocumentUploadUrlResponse model containing upload_url, document_id, and storage_path.

    Raises:
        StorageOperationError: If Supabase Storage signed URL creation fails.
    """
    safe_filename = sanitize_filename(request.file_name)
    document_id = uuid.uuid4()
    bucket_name = settings.STORAGE_BUCKET_NAME
    storage_path = f"{current_user.user_id}/{document_id}/{safe_filename}"
    now_utc = get_utc_now()

    new_doc = Document(
        document_id=document_id,
        user_id=current_user.user_id,
        file_name=request.file_name.strip(),
        bucket_name=bucket_name,
        storage_path=storage_path,
        status="PENDING",
        created_by=current_user.user_id,
        created_date=now_utc,
        last_modified_by=current_user.user_id,
        last_modified_date=now_utc
    )

    created_doc = document_repository.create_document(db=db, document=new_doc)

    try:
        upload_url = StorageService.create_signed_upload_url(
            bucket_name=bucket_name,
            storage_path=storage_path
        )
    except Exception as e:
        document_repository.delete_document(db=db, document=created_doc)
        raise StorageOperationError("Failed to generate secure upload URL.") from e

    return DocumentUploadUrlResponse(
        document_id=document_id,
        bucket_name=bucket_name,
        storage_path=storage_path,
        upload_url=upload_url,
        status="PENDING",
        expires_in=600,
        message="Upload URL generated successfully"
    )


def confirm_upload(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentConfirmUploadResponse:
    """
    Confirms that the client successfully uploaded file bytes to object storage.

    1. Fetches document metadata ensuring current user ownership.
    2. Verifies object liveness in storage via `StorageService.file_exists`.
    3. Updates document last_modified timestamp while retaining `PENDING` status.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User ORM instance.
        document_id: Unique UUID of document to confirm.

    Returns:
        DocumentConfirmUploadResponse model.

    Raises:
        DocumentNotFoundError: If document record is missing or not owned by user.
        ValidationError: If file object does not exist in storage bucket.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    file_exists = StorageService.file_exists(
        bucket_name=document.bucket_name,
        storage_path=document.storage_path
    )
    if not file_exists:
        raise ValidationError("Uploaded file not found in storage. Please upload file before confirming.")

    updated_doc = document_repository.update_document_status(
        db=db,
        document=document,
        new_status=document.status,
        last_modified_by=current_user.user_id
    )

    return DocumentConfirmUploadResponse(
        document_id=updated_doc.document_id,
        status=updated_doc.status,
        message="Document upload confirmed successfully"
    )


def list_user_documents(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None
) -> DocumentListResponse:
    """
    Fetches paginated list of documents owned by authenticated user.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model instance.
        page: Page number (1-based index).
        page_size: Page item limit (1 to 100).
        status_filter: Optional filter (PENDING, PROCESSING, COMPLETED, FAILED).

    Returns:
        DocumentListResponse model containing items array and pagination counts.

    Raises:
        ValidationError: If page or status parameters are invalid.
    """
    if page < 1:
        raise ValidationError("Page parameter must be greater than or equal to 1.")
    if page_size < 1 or page_size > 100:
        raise ValidationError("Page size must be between 1 and 100.")

    if status_filter:
        upper_status = status_filter.strip().upper()
        if upper_status not in ALLOWED_STATUSES:
            raise ValidationError(
                f"Invalid status filter '{status_filter}'. Allowed: PENDING, PROCESSING, COMPLETED, FAILED"
            )

    docs, total_items, total_pages = document_repository.list_user_documents(
        db=db,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )

    items = [DocumentListItemResponse.model_validate(doc) for doc in docs]

    return DocumentListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages
    )


def get_user_document(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentDetailResponse:
    """
    Fetches detailed metadata for a document owned by authenticated user.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Target document UUID.

    Returns:
        DocumentDetailResponse model.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    return DocumentDetailResponse.model_validate(document)


def generate_download_url(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentDownloadUrlResponse:
    """
    Generates temporary pre-signed download URL for private document file access (5-minute expiration).

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Target document UUID.

    Returns:
        DocumentDownloadUrlResponse model with signed download URL.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
        StorageOperationError: If storage signed URL generation fails.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    try:
        download_url = StorageService.create_signed_download_url(
            bucket_name=document.bucket_name,
            storage_path=document.storage_path,
            expires_in=300
        )
    except Exception as e:
        raise StorageOperationError("Failed to generate secure download URL.") from e

    return DocumentDownloadUrlResponse(
        document_id=document.document_id,
        file_name=document.file_name,
        download_url=download_url,
        expires_in=300
    )


def delete_user_document(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> None:
    """
    Safely deletes a document owned by authenticated user:

    1. Verifies ownership.
    2. Deletes child database records (`document_chunks` and `document_info`).
    3. Deletes physical file object from Supabase Storage bucket.
    4. Deletes parent Document record from database.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Target document UUID.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    # 1. Delete child records
    document_chunk_repository.delete_chunks_by_document_id(db=db, document_id=document.document_id)
    document_info_repository.delete_document_info_by_document_id(db=db, document_id=document.document_id)

    # 2. Delete storage file
    StorageService.delete_file(bucket_name=document.bucket_name, storage_path=document.storage_path)

    # 3. Delete Document metadata
    document_repository.delete_document(db=db, document=document)


class DocumentService:
    """Backward-compatible class wrapper around document_service functions."""

    @classmethod
    def initialize_upload(cls, db: Session, current_user: User, request: DocumentUploadUrlRequest) -> DocumentUploadUrlResponse:
        return initialize_upload(db=db, current_user=current_user, request=request)

    @classmethod
    def confirm_upload(cls, db: Session, current_user: User, document_id: uuid.UUID) -> DocumentConfirmUploadResponse:
        return confirm_upload(db=db, current_user=current_user, document_id=document_id)

    @classmethod
    def list_user_documents(cls, db: Session, current_user: User, page: int = 1, page_size: int = 10, status_filter: Optional[str] = None) -> DocumentListResponse:
        return list_user_documents(db=db, current_user=current_user, page=page, page_size=page_size, status_filter=status_filter)

    @classmethod
    def get_user_document(cls, db: Session, current_user: User, document_id: uuid.UUID) -> DocumentDetailResponse:
        return get_user_document(db=db, current_user=current_user, document_id=document_id)

    @classmethod
    def generate_download_url(cls, db: Session, current_user: User, document_id: uuid.UUID) -> DocumentDownloadUrlResponse:
        return generate_download_url(db=db, current_user=current_user, document_id=document_id)

    @classmethod
    def delete_user_document(cls, db: Session, current_user: User, document_id: uuid.UUID) -> None:
        delete_user_document(db=db, current_user=current_user, document_id=document_id)

