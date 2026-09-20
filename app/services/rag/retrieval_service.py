"""
Legacy Retrieval Service Module

Provides backward-compatible `RetrievalService` delegating to function-based `rag_service`.
Translates domain exceptions into HTTPExceptions for backward-compatible route/test calls.
"""

import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    ValidationError,
    AppException
)
from app.models.user import User
from app.schemas.document import DocumentRetrieveResponse
from app.services import rag_service


class RetrievalService:
    """Backward-compatible class wrapper around rag_service.retrieve_relevant_chunks."""

    @classmethod
    async def retrieve_relevant_chunks(
        cls,
        db: Session,
        current_user: User,
        document_id: uuid.UUID,
        question: str,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None
    ) -> DocumentRetrieveResponse:
        try:
            return await rag_service.retrieve_relevant_chunks(
                db=db,
                current_user=current_user,
                document_id=document_id,
                question=question,
                top_k=top_k,
                similarity_threshold=similarity_threshold
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
