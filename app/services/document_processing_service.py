"""
Document Processing Service Module

Provides function-based workflow orchestration for the document intelligence processing pipeline:
Supabase Storage Download -> OCR Text Extraction -> LLM Information Extraction ->
`document_info` Persistence -> Text Cleaning & Chunking -> Embedding Generation & Vector Storage -> Status COMPLETED.
"""

import logging
import uuid
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyProcessingError,
    DocumentProcessingError
)
from app.models.document_info import DocumentInfo
from app.models.user import User
from app.repositories import (
    document_repository,
    document_info_repository
)
from app.schemas.document import DocumentInfoResponse, DocumentInfoUpdateRequest
from app.services import chunking_service, embedding_service
from app.services.ocr import get_ocr_provider, OCRResult
from app.services.llm import get_llm_provider
from app.services.storage_service import StorageService
from app.utils.file_validation import guess_mime_type
from app.utils.datetime_utils import get_utc_now

logger = logging.getLogger(__name__)


async def process_document(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> OCRResult:
    """
    Executes end-to-end processing pipeline for a document owned by authenticated user.

    Pipeline Steps:
    1. Verifies document existence & user ownership via `document_repository`.
    2. Prevents concurrent processing if status is already `PROCESSING`.
    3. Updates status to `PROCESSING`.
    4. Downloads object bytes from private storage bucket using `StorageService`.
    5. Invokes OCR Provider for raw text & page extraction.
    6. Invokes LLM Provider for structured driving licence schema extraction.
    7. Persists structured fields in `public.document_info` via `document_info_repository`.
    8. Cleans raw text, splits into overlapping chunks, and persists into `public.document_chunks`.
    9. Generates 1536-dim vector embeddings and stores them in `public.document_chunks`.
    10. Updates status to `COMPLETED`.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model instance.
        document_id: Unique UUID identifier of target document.

    Returns:
        Structured OCRResult payload.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
        DocumentAlreadyProcessingError: If document status is already PROCESSING.
        DocumentProcessingError: If any pipeline stage (download, OCR, LLM, chunking, embedding) fails.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    if document.status == "PROCESSING":
        raise DocumentAlreadyProcessingError("Document is currently being processed.")

    # Transition status to PROCESSING
    document_repository.update_document_status(
        db=db,
        document=document,
        new_status="PROCESSING",
        last_modified_by=current_user.user_id
    )

    # Step 1: Download file bytes from storage
    try:
        file_bytes = StorageService.download_file(
            bucket_name=document.bucket_name,
            storage_path=document.storage_path
        )
    except Exception as e:
        logger.error(f"Storage download failed for document '{document_id}': {e}")
        document_repository.update_document_status(
            db=db, document=document, new_status="FAILED", last_modified_by=current_user.user_id
        )
        raise DocumentProcessingError("Document file is missing or unreadable in storage.") from e

    mime_type = guess_mime_type(document.file_name)

    # Step 2: OCR Text Extraction
    ocr_provider = get_ocr_provider()
    try:
        ocr_result = await ocr_provider.extract_text(
            file_bytes=file_bytes,
            file_name=document.file_name,
            mime_type=mime_type,
            document_id=document.document_id
        )
        logger.info(
            f"Pipeline Step 2/8 complete: OCR text extraction finished for document '{document_id}' "
            f"using OCR engine provider='{ocr_result.provider}' (extracted {len(ocr_result.text)} chars)."
        )
    except Exception as e:
        logger.error(f"OCR execution failed for document '{document_id}': {e}")
        document_repository.update_document_status(
            db=db, document=document, new_status="FAILED", last_modified_by=current_user.user_id
        )
        raise DocumentProcessingError("OCR text extraction failed.") from e

    # Step 3: LLM Structured Information Extraction (Primary: Gemini, Fallback: Groq)
    llm_provider = get_llm_provider()
    try:
        extraction_schema = await llm_provider.extract_info(
            ocr_text=ocr_result.text,
            document_id=document.document_id
        )
    except Exception as e:
        logger.error(f"LLM extraction failed for document '{document_id}': {e}")
        document_repository.update_document_status(
            db=db, document=document, new_status="FAILED", last_modified_by=current_user.user_id
        )
        raise DocumentProcessingError("LLM structured information extraction failed.") from e

    # Step 4: Persist extracted info into public.document_info
    now_utc = get_utc_now()
    existing_info = document_info_repository.get_document_info_by_document_id(
        db=db, document_id=document.document_id
    )

    if existing_info:
        existing_info.licence_number = extraction_schema.licence_number
        existing_info.full_name = extraction_schema.full_name
        existing_info.parent_name = extraction_schema.parent_name
        existing_info.date_of_birth = extraction_schema.date_of_birth
        existing_info.blood_group = extraction_schema.blood_group
        existing_info.address = extraction_schema.address
        existing_info.issue_date = extraction_schema.issue_date
        existing_info.expiry_date = extraction_schema.expiry_date
        existing_info.vehicle_authorization = extraction_schema.vehicle_authorization
        existing_info.issuing_authority = extraction_schema.issuing_authority
        existing_info.restrictions = extraction_schema.restrictions
        existing_info.other_information = extraction_schema.other_information
        existing_info.last_modified_by = current_user.user_id
        existing_info.last_modified_date = now_utc
        document_info_repository.upsert_document_info(db=db, document_info=existing_info)
    else:
        new_info = DocumentInfo(
            document_info_id=uuid.uuid4(),
            document_id=document.document_id,
            licence_number=extraction_schema.licence_number,
            full_name=extraction_schema.full_name,
            parent_name=extraction_schema.parent_name,
            date_of_birth=extraction_schema.date_of_birth,
            blood_group=extraction_schema.blood_group,
            address=extraction_schema.address,
            issue_date=extraction_schema.issue_date,
            expiry_date=extraction_schema.expiry_date,
            vehicle_authorization=extraction_schema.vehicle_authorization,
            issuing_authority=extraction_schema.issuing_authority,
            restrictions=extraction_schema.restrictions,
            other_information=extraction_schema.other_information,
            created_by=current_user.user_id,
            created_date=now_utc,
            last_modified_by=current_user.user_id,
            last_modified_date=now_utc
        )
        document_info_repository.upsert_document_info(db=db, document_info=new_info)

    # Step 5 & 6: Clean OCR text, create chunks, and persist
    try:
        chunking_service.process_and_save_chunks(
            db=db,
            current_user=current_user,
            document_id=document.document_id,
            raw_ocr_text=ocr_result.text,
            pages_data=ocr_result.pages
        )
    except Exception as e:
        logger.error(f"Text cleaning/chunking failed for document '{document_id}': {e}")
        document_repository.update_document_status(
            db=db, document=document, new_status="FAILED", last_modified_by=current_user.user_id
        )
        raise DocumentProcessingError("Text chunking and persistence failed.") from e

    # Step 7: Generate dense vector embeddings and update vector columns via Google Gemini
    try:
        embedding_provider = embedding_service.get_embedding_provider()
        logger.info(
            f"Pipeline Step 7/8: Generating vector embeddings for document '{document.document_id}' "
            f"using Gemini embedding model='{embedding_provider.model}'..."
        )
        await embedding_service.generate_and_store_embeddings(
            db=db,
            current_user=current_user,
            document_id=document.document_id
        )
        logger.info(
            f"Pipeline Step 7/8 complete: Gemini vector embeddings generated for document '{document.document_id}'."
        )
    except Exception as e:
        logger.error(f"Gemini embedding generation failed for document '{document_id}': {e}")
        document_repository.update_document_status(
            db=db, document=document, new_status="FAILED", last_modified_by=current_user.user_id
        )
        raise DocumentProcessingError("Embedding generation and vector storage failed.") from e

    # Step 8: Update document status to COMPLETED
    document_repository.update_document_status(
        db=db,
        document=document,
        new_status="COMPLETED",
        last_modified_by=current_user.user_id
    )

    return ocr_result


def get_document_info(
    db: Session,
    current_user: User,
    document_id: uuid.UUID
) -> DocumentInfoResponse:
    """
    Fetches structured driving licence information for a document owned by authenticated user.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Unique UUID identifier of document.

    Returns:
        DocumentInfoResponse model.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
        DocumentProcessingError: If structured information has not yet been extracted.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    doc_info = document_info_repository.get_document_info_by_document_id(
        db=db,
        document_id=document_id
    )
    if not doc_info:
        raise DocumentNotFoundError("Extracted document information not found. Please run processing first.")

    return DocumentInfoResponse.model_validate(doc_info)


def update_document_info(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    request: DocumentInfoUpdateRequest
) -> DocumentInfoResponse:
    """
    Updates extracted driving licence information for a document owned by authenticated user.
    Sets last_modified_by to current_user.email.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Unique UUID identifier of document.
        request: DocumentInfoUpdateRequest payload.

    Returns:
        Updated DocumentInfoResponse model.

    Raises:
        DocumentNotFoundError: If document or document_info is not found.
    """
    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    doc_info = document_info_repository.get_document_info_by_document_id(
        db=db,
        document_id=document_id
    )
    if not doc_info:
        doc_info = DocumentInfo(
            document_id=document_id,
            created_by=current_user.user_id,
            created_date=get_utc_now()
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(doc_info, field):
            setattr(doc_info, field, value)

    doc_info.last_modified_by = current_user.email
    doc_info.last_modified_date = get_utc_now()

    updated_info = document_info_repository.upsert_document_info(db=db, document_info=doc_info)
    return DocumentInfoResponse.model_validate(updated_info)


class DocumentProcessingService:
    """Backward-compatible class wrapper around document_processing_service functions."""

    @classmethod
    async def process_document(cls, db: Session, current_user: User, document_id: uuid.UUID) -> OCRResult:
        return await process_document(db=db, current_user=current_user, document_id=document_id)

    @classmethod
    def get_document_info(cls, db: Session, current_user: User, document_id: uuid.UUID) -> DocumentInfoResponse:
        return get_document_info(db=db, current_user=current_user, document_id=document_id)

    @classmethod
    def update_document_info(cls, db: Session, current_user: User, document_id: uuid.UUID, request: DocumentInfoUpdateRequest) -> DocumentInfoResponse:
        return update_document_info(db=db, current_user=current_user, document_id=document_id, request=request)


