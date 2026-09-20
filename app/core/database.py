from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# Create SQLAlchemy engine using DATABASE_URL from settings.
# pool_pre_ping=True tests connections for liveness before giving them to the application.
# connect_timeout=5 ensures database connection attempts fail fast rather than hanging indefinitely.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 5},
    echo=False
)

# Session factory bound to the engine.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all ORM model definitions.
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per HTTP request.
    Ensures the session is cleanly closed after request completion or if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
