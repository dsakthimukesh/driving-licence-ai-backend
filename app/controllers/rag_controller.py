"""
RAG Controller Module

Handles HTTP-level request orchestration for vector retrieval and grounded RAG Q&A endpoints.
Translates domain exceptions into standard HTTP error responses.
"""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    ValidationError,
    AppException
)
from app.models.user import User
from app.schemas.document import (
    DocumentRetrieveRequest,
    DocumentRetrieveResponse,
    DocumentQARequest,
    DocumentQAResponse
)
from app.services import rag_service


async def handle_retrieve_chunks(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    request: DocumentRetrieveRequest
) -> DocumentRetrieveResponse:
    """Controller function for retrieving relevant document chunks via vector similarity search."""
    try:
        return await rag_service.retrieve_relevant_chunks(
            db=db,
            current_user=current_user,
            document_id=document_id,
            question=request.question,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
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


async def handle_ask_question(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    request: DocumentQARequest
) -> DocumentQAResponse:
    """Controller function for executing grounded RAG question-answering."""
    try:
        return await rag_service.answer_document_question(
            db=db,
            current_user=current_user,
            document_id=document_id,
            question=request.question,
            top_k=request.top_k
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
