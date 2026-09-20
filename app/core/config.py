import os
import shutil
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application core configuration powered by Pydantic Settings.
    Automatically reads environment variables from system env or local `.env` file.
    """

    # Application settings
    APP_NAME: str = Field(
        default="Driving Licence AI",
        description="Application title used across OpenAPI documentation and response payloads."
    )
    APP_ENV: str = Field(
        default="development",
        description="Runtime environment mode (development, staging, production)."
    )
    CORS_ORIGINS: str = Field(
        default="*",
        description="Allowed CORS origins for cross-origin API requests (comma-separated or '*' for all)."
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string for direct backend database connections."
    )

    # Supabase Configuration
    SUPABASE_URL: str = Field(
        ...,
        description="Base HTTPS URL for Supabase API services."
    )
    SUPABASE_SERVICE_KEY: str = Field(
        ...,
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
        description="Supabase Service Role Key for administrative and backend Storage/DB access."
    )

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = Field(
        ...,
        description="Secret key used for signing and verifying backend JWT access tokens."
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Cryptographic algorithm for signing JWT tokens."
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Validity period of generated access tokens in minutes."
    )

    # Supabase Storage Bucket Configuration
    STORAGE_BUCKET_NAME: str = Field(
        default="documents",
        description="Name of the Supabase Storage bucket reserved for uploaded driving licence files."
    )

    # AWS Textract OCR Configuration (Optional)
    AWS_REGION: Optional[str] = Field(
        default="us-east-1",
        description="AWS Region for AWS Textract service."
    )
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID for Textract OCR operations."
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key for Textract OCR operations."
    )
    OCR_PROVIDER: str = Field(
        default="auto",
        description="OCR provider selection mode ('auto', 'aws_textract', 'local')."
    )
    TESSERACT_CMD: str = Field(
        default_factory=lambda: os.getenv("TESSERACT_CMD") or shutil.which("tesseract") or "/usr/bin/tesseract",
        description="Path to local Tesseract OCR executable binary."
    )

    # Primary & Fallback LLM Provider Configuration
    PRIMARY_LLM_PROVIDER: str = Field(
        default="gemini",
        description="Primary LLM provider name ('gemini', 'groq')."
    )
    FALLBACK_LLM_PROVIDER: str = Field(
        default="groq",
        description="Fallback LLM provider name ('groq', 'none')."
    )

    # Google Gemini AI Configuration
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        description="Google Gemini API Key for LLM structured extraction, embeddings, and RAG QA."
    )
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Fallback alias for Google Gemini API Key."
    )
    GEMINI_GENERATION_MODEL: str = Field(
        default="gemini-3.6-flash",
        description="Google Gemini model name for information extraction and RAG QA generation."
    )
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-001",
        description="Google Gemini model name producing dense vector embeddings."
    )

    # Groq LLM Fallback Configuration
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API Key for LLM fallback structured extraction and RAG QA."
    )
    GROQ_GENERATION_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model name used for fallback extraction and RAG QA generation."
    )

    # Text Chunking Configuration
    CHUNK_SIZE: int = Field(
        default=500,
        description="Target maximum character size per document chunk."
    )
    CHUNK_OVERLAP: int = Field(
        default=100,
        description="Character overlap between consecutive document chunks."
    )

    # Embedding Generation & Vector Storage Configuration
    EMBEDDING_DIMENSIONS: int = Field(
        default=1536,
        description="Target vector dimension size matching PostgreSQL VECTOR(1536) column."
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=20,
        description="Maximum number of document text chunks to include in a single batch embedding request."
    )

    # RAG Question-Answering Configuration
    RAG_MAX_CONTEXT_LENGTH: int = Field(
        default=4000,
        description="Maximum character length of formatted retrieved context string passed to LLM."
    )
    RAG_DEFAULT_TOP_K: int = Field(
        default=5,
        description="Default top_k chunks retrieved for question answering."
    )
    RAG_MAX_TOP_K: int = Field(
        default=20,
        description="Maximum allowed top_k value for question answering."
    )
    RAG_TEMPERATURE: float = Field(
        default=0.0,
        description="LLM temperature setting for deterministic, grounded RAG Q&A generation."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Instantiate settings instance
settings = Settings()
