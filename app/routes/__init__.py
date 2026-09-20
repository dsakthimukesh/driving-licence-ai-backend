"""
Routes Package

Exports APIRouters for Authentication, Document Management, and RAG.
"""

from app.routes.auth_routes import router as auth_router
from app.routes.document_routes import router as document_router
from app.routes.rag_routes import router as rag_router

__all__ = [
    "auth_router",
    "document_router",
    "rag_router",
]
