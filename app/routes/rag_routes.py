"""
RAG Routes Module

Defines HTTP routes for RAG vector retrieval and grounded question answering against document chunks.
Delegates execution to `app.controllers.rag_controller`.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentRetrieveRequest,
    DocumentRetrieveResponse,
    DocumentQARequest,
    DocumentQAResponse
)
from app.controllers import rag_controller

router = APIRouter()


@router.post(
    "/{document_id}/retrieve",
    response_model=DocumentRetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relevant document chunks via vector similarity search",
    description="Generates embedding for user question and executes pgvector similarity search against document chunks."
)
async def retrieve_document_chunks(
    document_id: uuid.UUID,
    request: DocumentRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves relevant document chunks. Delegates to rag_controller.handle_retrieve_chunks."""
    return await rag_controller.handle_retrieve_chunks(
        db=db,
        current_user=current_user,
        document_id=document_id,
        request=request
    )


@router.post(
    "/{document_id}/ask",
    response_model=DocumentQAResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer question about a document using grounded RAG",
    description="Retrieves relevant document chunks and generates a grounded answer supported by source citations."
)
async def ask_document_question(
    document_id: uuid.UUID,
    request: DocumentQARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes grounded RAG question answering. Delegates to rag_controller.handle_ask_question."""
    return await rag_controller.handle_ask_question(
        db=db,
        current_user=current_user,
        document_id=document_id,
        request=request
    )
