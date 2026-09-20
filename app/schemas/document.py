import os
import uuid
from datetime import date, datetime
from typing import List, Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator

# Allowed MIME types and size limit constants
ALLOWED_MIME_TYPES: Set[str] = {
    "application/pdf",
    "image/jpeg",
    "image/png"
}

ALLOWED_EXTENSIONS_MAP = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"}
}

ALLOWED_STATUSES: Set[str] = {
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED"
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


class DocumentUploadUrlRequest(BaseModel):
    """
    Request payload schema for initializing document pre-signed upload URL.
    Validates file metadata (filename, MIME type, file size, and extension matching).
    """
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original name of the file to be uploaded."
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file (application/pdf, image/jpeg, image/png)."
    )
    file_size_bytes: int = Field(
        ...,
        gt=0,
        le=MAX_FILE_SIZE_BYTES,
        description="File size in bytes (maximum 10 MB / 10,485,760 bytes)."
    )

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("File name cannot be empty or whitespace.")
        basename = os.path.basename(cleaned)
        if not basename:
            raise ValueError("Invalid file name.")
        return basename

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Unsupported MIME type '{v}'. Allowed MIME types: application/pdf, image/jpeg, image/png."
            )
        return cleaned

    @model_validator(mode="after")
    def validate_extension_matches_mime(self):
        ext = os.path.splitext(self.file_name)[1].lower()
        if not ext:
            raise ValueError("File name must include a valid file extension (e.g. .pdf, .jpg, .png).")

        allowed_exts = ALLOWED_EXTENSIONS_MAP.get(self.mime_type, set())
        if ext not in allowed_exts:
            raise ValueError(
                f"File extension '{ext}' does not match the provided MIME type '{self.mime_type}'. "
                f"Expected extension in {allowed_exts}."
            )
        return self


class DocumentUploadUrlResponse(BaseModel):
    """
    Response payload schema containing generated pre-signed upload URL and document metadata.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Generated unique document identifier (UUID)."
    )
    bucket_name: str = Field(
        ...,
        description="Supabase Storage bucket name."
    )
    storage_path: str = Field(
        ...,
        description="Generated object storage path in Supabase Storage."
    )
    upload_url: str = Field(
        ...,
        description="Temporary pre-signed URL for direct browser/client file upload."
    )
    status: str = Field(
        default="PENDING",
        description="Initial document workflow status."
    )
    expires_in: int = Field(
        default=600,
        description="Upload URL expiration time in seconds (10 minutes)."
    )
    message: str = Field(
        default="Upload URL generated successfully",
        description="Status message."
    )


class DocumentConfirmUploadResponse(BaseModel):
    """
    Response payload schema for upload confirmation.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Confirmed document unique identifier (UUID)."
    )
    status: str = Field(
        default="PENDING",
        description="Confirmed document workflow status (ready for AI processing)."
    )
    message: str = Field(
        default="Document upload confirmed successfully",
        description="Status message."
    )


class DocumentListItemResponse(BaseModel):
    """
    Item schema inside paginated document list response.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    file_name: str = Field(
        ...,
        description="Original name of the file."
    )
    bucket_name: str = Field(
        ...,
        description="Supabase Storage bucket name."
    )
    storage_path: str = Field(
        ...,
        description="Object path in storage bucket."
    )
    status: str = Field(
        ...,
        description="Current workflow status (PENDING, PROCESSING, COMPLETED, FAILED)."
    )
    created_date: datetime = Field(
        ...,
        description="Timestamp when document record was created."
    )
    last_modified_date: datetime = Field(
        ...,
        description="Timestamp when document record was last modified."
    )

    model_config = {
        "from_attributes": True
    }


class DocumentListResponse(BaseModel):
    """
    Paginated list response for GET /api/v1/documents.
    """
    items: List[DocumentListItemResponse] = Field(
        ...,
        description="List of document metadata items."
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-based)."
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Page size limit."
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total matching items across all pages."
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages."
    )


class DocumentDetailResponse(BaseModel):
    """
    Detailed document metadata response for GET /api/v1/documents/{document_id}.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    file_name: str = Field(
        ...,
        description="Original file name."
    )
    bucket_name: str = Field(
        ...,
        description="Supabase Storage bucket name."
    )
    storage_path: str = Field(
        ...,
        description="Object path in storage bucket."
    )
    status: str = Field(
        ...,
        description="Current workflow status."
    )
    created_date: datetime = Field(
        ...,
        description="Timestamp when document record was created."
    )
    last_modified_date: datetime = Field(
        ...,
        description="Timestamp when document record was last modified."
    )

    model_config = {
        "from_attributes": True
    }


class DocumentDownloadUrlResponse(BaseModel):
    """
    Response schema for GET /api/v1/documents/{document_id}/download-url.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    file_name: str = Field(
        ...,
        description="Original file name."
    )
    download_url: str = Field(
        ...,
        description="Temporary pre-signed URL for direct browser/client file download."
    )
    expires_in: int = Field(
        default=300,
        description="Download URL expiration time in seconds (5 minutes)."
    )


class DocumentInfoUpdateRequest(BaseModel):
    """
    Request payload schema for updating extracted driving licence information.
    """
    licence_number: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    parent_name: Optional[str] = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    blood_group: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    issue_date: Optional[date] = Field(default=None)
    expiry_date: Optional[date] = Field(default=None)
    vehicle_authorization: Optional[str] = Field(default=None)
    issuing_authority: Optional[str] = Field(default=None)
    restrictions: Optional[str] = Field(default=None)
    other_information: Optional[str] = Field(default=None)


class DocumentInfoResponse(BaseModel):
    """
    Response schema for GET /api/v1/documents/{document_id}/info.
    Returns structured driving licence fields stored in public.document_info.
    """
    document_info_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the document info record."
    )
    document_id: uuid.UUID = Field(
        ...,
        description="Associated document unique identifier (UUID)."
    )
    licence_number: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    parent_name: Optional[str] = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    blood_group: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    issue_date: Optional[date] = Field(default=None)
    expiry_date: Optional[date] = Field(default=None)
    vehicle_authorization: Optional[str] = Field(default=None)
    issuing_authority: Optional[str] = Field(default=None)
    restrictions: Optional[str] = Field(default=None)
    other_information: Optional[str] = Field(default=None)
    created_date: datetime = Field(...)
    last_modified_by: Optional[str] = Field(default=None)
    last_modified_date: datetime = Field(...)

    model_config = {
        "from_attributes": True
    }


class DocumentRetrieveRequest(BaseModel):
    """
    Request payload schema for POST /api/v1/documents/{document_id}/retrieve.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language user question to search against document chunks."
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of relevant document chunks to retrieve (1 to 20)."
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Optional minimum cosine similarity score threshold (0.0 to 1.0)."
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or whitespace-only.")
        return cleaned


class RetrievedChunkResult(BaseModel):
    """
    Schema representing a single retrieved document chunk with vector similarity score.
    """
    document_chunk_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the document chunk."
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="0-based index reflecting chronological position of chunk."
    )
    content: str = Field(
        ...,
        description="Text content of the retrieved chunk."
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Source 1-based page number if available."
    )
    similarity_score: float = Field(
        ...,
        description="Cosine similarity score (higher is more similar, max 1.0)."
    )


class DocumentRetrieveResponse(BaseModel):
    """
    Response schema for POST /api/v1/documents/{document_id}/retrieve.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    question: str = Field(
        ...,
        description="Cleaned original question string."
    )
    results: List[RetrievedChunkResult] = Field(
        ...,
        description="List of relevant document chunks ordered by similarity score descending."
    )
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of relevant chunks returned."
    )


class DocumentQARequest(BaseModel):
    """
    Request payload schema for POST /api/v1/documents/{document_id}/ask.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language question about the document."
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top relevant context chunks to retrieve for Q&A (1 to 20)."
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or whitespace-only.")
        return cleaned


class SourceReference(BaseModel):
    """
    Citation source chunk reference schema for RAG Q&A response.
    """
    document_chunk_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the cited document chunk."
    )
    page_number: Optional[int] = Field(
        default=None,
        description="1-based page index from source document if available."
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="0-based sequential chunk position index."
    )
    similarity_score: float = Field(
        ...,
        description="Cosine similarity score."
    )
    content: str = Field(
        ...,
        description="Content snippet of the cited source chunk."
    )


class DocumentQAResponse(BaseModel):
    """
    Response schema for POST /api/v1/documents/{document_id}/ask.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="Document unique identifier (UUID)."
    )
    question: str = Field(
        ...,
        description="Cleaned user question string."
    )
    answer: str = Field(
        ...,
        description="Grounded AI answer generated strictly from retrieved document context."
    )
    sources: List[SourceReference] = Field(
        ...,
        description="List of source document chunk citations supporting the generated answer."
    )


