"""
Legacy QA Service Module

Provides backward-compatible `QAService` delegating to function-based `rag_service`.
Translates domain exceptions into HTTPExceptions for backward-compatible route/test calls.
"""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    ValidationError,
    AppException
)
from app.models.user import User
from app.schemas.document import DocumentQAResponse
from app.services import rag_service
from app.services.llm import get_llm_provider


class QAService:
    """Backward-compatible class wrapper around rag_service.answer_document_question."""

    @classmethod
    async def answer_document_question(
        cls,
        db: Session,
        current_user: User,
        document_id: uuid.UUID,
        question: str,
        top_k: int = 5
    ) -> DocumentQAResponse:
        try:
            return await rag_service.answer_document_question(
                db=db,
                current_user=current_user,
                document_id=document_id,
                question=question,
                top_k=top_k
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
