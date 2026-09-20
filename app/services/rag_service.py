"""
RAG Service Module

Provides function-based business logic for RAG vector retrieval and grounded question answering.
Integrates embedding generation, pgvector cosine similarity search, context construction, and LLM Q&A prompts.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    ValidationError
)
from app.models.user import User
from app.repositories import document_repository, document_chunk_repository
from app.schemas.document import (
    DocumentRetrieveResponse,
    RetrievedChunkResult,
    DocumentQAResponse,
    SourceReference
)
from app.services.embeddings import get_embedding_provider
import app.services.rag.qa_service as qa_service_mod
from app.services.rag.prompts import build_rag_qa_prompt


async def retrieve_relevant_chunks(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    question: str,
    top_k: int = 3,
    similarity_threshold: Optional[float] = None
) -> DocumentRetrieveResponse:
    """
    Performs vector similarity search against chunks of a document owned by authenticated user.

    1. Validates user document ownership via `document_repository`.
    2. Generates a 1536-dimensional embedding vector for the question text.
    3. Executes pgvector cosine similarity search via `document_chunk_repository`.
    4. Filters and formats matching chunks above similarity threshold.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Unique UUID identifier of target document.
        question: User query string.
        top_k: Maximum number of top chunks to retrieve.
        similarity_threshold: Optional minimum cosine similarity score threshold.

    Returns:
        DocumentRetrieveResponse model containing retrieved chunks and similarity scores.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
        ValidationError: If question parameter is empty.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValidationError("Question parameter cannot be empty.")

    if top_k < 1 or top_k > 20:
        raise ValidationError("top_k limit must be an integer between 1 and 20.")

    document = document_repository.get_user_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.user_id
    )
    if not document:
        raise DocumentNotFoundError("Document not found")

    # Generate question embedding
    embedding_provider = get_embedding_provider()
    question_embeddings = await embedding_provider.generate_embeddings([cleaned_question])
    question_embedding = question_embeddings[0]

    # Execute vector similarity query
    raw_results = document_chunk_repository.get_similar_chunks(
        db=db,
        document_id=document_id,
        query_embedding=question_embedding,
        top_k=top_k
    )

    results: List[RetrievedChunkResult] = []
    for chunk, score in raw_results:
        if similarity_threshold is not None and score < similarity_threshold:
            continue
        results.append(
            RetrievedChunkResult(
                document_chunk_id=chunk.document_chunk_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                similarity_score=round(score, 4)
            )
        )

    return DocumentRetrieveResponse(
        document_id=document_id,
        question=cleaned_question,
        results=results,
        total_results=len(results)
    )


async def answer_document_question(
    db: Session,
    current_user: User,
    document_id: uuid.UUID,
    question: str,
    top_k: int = 3
) -> DocumentQAResponse:
    """
    Answers a question about a document using grounded RAG retrieval and LLM context prompt generation.

    1. Retrieves top-k relevant document chunks via pgvector similarity search.
    2. Builds structured context string and citation source list.
    3. Renders grounded RAG prompt ensuring answer strictly cites context facts.
    4. Invokes LLM provider for response generation.

    Args:
        db: Active SQLAlchemy database session.
        current_user: Authenticated User model.
        document_id: Target document UUID.
        question: User query string.
        top_k: Maximum context chunks to retrieve.

    Returns:
        DocumentQAResponse model containing grounded answer and citations.

    Raises:
        DocumentNotFoundError: If document is missing or not owned by user.
    """
    retrieval_res = await retrieve_relevant_chunks(
        db=db,
        current_user=current_user,
        document_id=document_id,
        question=question,
        top_k=top_k,
        similarity_threshold=None
    )

    chunks = retrieval_res.results

    if not chunks:
        return DocumentQAResponse(
            document_id=document_id,
            question=question,
            answer="The requested information is not mentioned in the provided document.",
            sources=[]
        )

    # Format context and sources
    context_blocks = []
    sources: List[SourceReference] = []

    for idx, c in enumerate(chunks, 1):
        context_blocks.append(f"[Source {idx} - Page {c.page_number or 1}]:\n{c.content}")
        sources.append(
            SourceReference(
                document_chunk_id=c.document_chunk_id,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                similarity_score=c.similarity_score,
                content=c.content
            )
        )

    context_str = "\n\n".join(context_blocks)
    llm_provider = qa_service_mod.get_llm_provider()
    try:
        answer_text = await llm_provider.generate_rag_answer(
            question=question,
            formatted_context=context_str
        )
    except Exception as e:
        raise DocumentProcessingError("LLM question answering failed.") from e

    return DocumentQAResponse(
        document_id=document_id,
        question=question,
        answer=answer_text,
        sources=sources
    )
