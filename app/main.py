from fastapi import FastAPI, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.routes.auth_routes import router as auth_router
from app.routes.document_routes import router as document_router
from app.routes.rag_routes import router as rag_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Driving Licence AI Document Intelligence API",
    version="0.1.0",
)

# Configure CORS Middleware
cors_origins_list = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list if cors_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(rag_router, prefix="/api/v1/documents", tags=["RAG"])


@app.get("/health", tags=["Health Checks"])
def health_check(response: Response, db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API server status and PostgreSQL database connection.
    Defined as a synchronous function (`def`) so FastAPI runs database I/O in a background
    threadpool, preventing event loop blocking.
    Returns 503 Service Unavailable if database connection fails.
    """
    try:
        # Execute lightweight SELECT 1 query to verify active DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "app": settings.APP_NAME,
        "database": db_status
    }
