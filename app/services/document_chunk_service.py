"""
Document Chunk Service Module (Legacy Wrapper)

Provides backward-compatible `DocumentChunkService` methods delegating to the function-based
`chunking_service` and `embedding_service` routines.
"""

import uuid
from typing import List
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.repositories import document_chunk_repository
from app.services import chunking_service, embedding_service
from app.services.chunking import ChunkPayload
from app.services.embeddings import get_embedding_provider


class DocumentChunkService:
    """
    Backward-compatible class wrapper around function-based chunking and embedding services.
    """

    @classmethod
    def save_document_chunks(
        cls,
        db: Session,
        current_user: User,
        document_id: uuid.UUID,
        chunks: List[ChunkPayload]
    ) -> List[DocumentChunk]:
        """
        Persists extracted text chunks for a document owned by the authenticated user.
        """
        # Delete existing chunks for idempotency
        document_chunk_repository.delete_chunks_by_document_id(db=db, document_id=document_id)

        from app.utils.datetime_utils import get_utc_now
        now_utc = get_utc_now()
        chunk_models: List[DocumentChunk] = []

        for c in chunks:
            clean_content = c.content.strip()
            if not clean_content:
                continue
            chunk_models.append(
                DocumentChunk(
                    document_chunk_id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=c.chunk_index,
                    content=clean_content,
                    page_number=c.page_number,
                    embedding=None,
                    created_by=current_user.user_id,
                    created_date=now_utc,
                    last_modified_by=current_user.user_id,
                    last_modified_date=now_utc
                )
            )
        return document_chunk_repository.save_chunks(db=db, chunks=chunk_models)

    @classmethod
    def get_document_chunks(
        cls,
        db: Session,
        current_user: User,
        document_id: uuid.UUID
    ) -> List[DocumentChunk]:
        """
        Fetches all text chunks for a document owned by the authenticated user sorted by chunk_index.
        """
        return document_chunk_repository.get_chunks_by_document_id(db=db, document_id=document_id)

    @classmethod
    async def generate_and_store_embeddings(
        cls,
        db: Session,
        current_user: User,
        document_id: uuid.UUID,
        force_regenerate: bool = False
    ) -> List[DocumentChunk]:
        """
        Generates dense vector embeddings for document chunks and persists vectors into PostgreSQL.
        """
        await embedding_service.generate_and_store_embeddings(
            db=db,
            current_user=current_user,
            document_id=document_id
        )
        return document_chunk_repository.get_chunks_by_document_id(db=db, document_id=document_id)
