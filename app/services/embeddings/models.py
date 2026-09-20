from typing import List
from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    """
    Structured model holding generated embeddings and metadata.
    """
    embeddings: List[List[float]] = Field(
        ...,
        description="List of float vector embeddings."
    )
    model: str = Field(
        ...,
        description="Name of the embedding model used."
    )
    dimensions: int = Field(
        ...,
        ge=1,
        description="Dimension length of each embedding vector."
    )
    execution_time_ms: int = Field(
        ...,
        ge=0,
        description="Total execution time in milliseconds."
    )
