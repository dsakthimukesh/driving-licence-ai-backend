import asyncio
import logging
from typing import List, Optional
from google import genai
from google.genai import types, errors

from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


async def _execute_with_retry(func, *args, max_retries: int = 4, initial_delay: float = 1.0, **kwargs):
    """
    Executes a synchronous function in an async thread pool with exponential backoff retries for transient Gemini API errors (e.g. 503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED).
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except (errors.APIError, errors.ClientError, errors.ServerError) as e:
            err_msg = str(e)
            is_transient = any(
                code in err_msg
                for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "temporarily unavailable", "high demand"]
            )
            if is_transient and attempt < max_retries:
                logger.warning(
                    f"Gemini API transient error (attempt {attempt}/{max_retries}): {e}. Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2.0
            else:
                raise e


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google Gemini Embedding Provider using `google-genai` SDK.
    Generates 1536-dimensional dense float vector embeddings.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else (settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY)
        self.model = model if model is not None else settings.GEMINI_EMBEDDING_MODEL
        self.expected_dimensions = settings.EMBEDDING_DIMENSIONS
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if not self.api_key or not str(self.api_key).strip():
            raise ValueError("Google Gemini API key is missing. Please set GEMINI_API_KEY in environment configuration.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        client = self._get_client()
        all_embeddings: List[List[float]] = []

        config = types.EmbedContentConfig(output_dimensionality=self.expected_dimensions)

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            try:
                response = await _execute_with_retry(
                    client.models.embed_content,
                    model=self.model,
                    contents=batch,
                    config=config
                )

                if not response or not response.embeddings:
                    raise ValueError("Gemini embedding API returned an empty response.")

                batch_vectors = [[float(v) for v in emb.values] for emb in response.embeddings]

                # Validate vector dimensions strictly
                for idx, vec in enumerate(batch_vectors):
                    if len(vec) != self.expected_dimensions:
                        raise ValueError(
                            f"Embedding vector dimension mismatch: expected {self.expected_dimensions}, "
                            f"got {len(vec)} for batch item {idx}."
                        )

                all_embeddings.extend(batch_vectors)

            except (errors.APIError, errors.ClientError, errors.ServerError) as e:
                logger.error(f"Gemini API error during embedding generation for batch starting at {i}: {e}")
                raise RuntimeError(f"Gemini API error during embedding generation: {str(e)}") from e
            except ValueError as e:
                logger.error(f"Gemini embedding validation error: {e}")
                raise e
            except Exception as e:
                logger.error(f"Gemini embedding generation failed for batch starting at {i}: {e}")
                raise RuntimeError(f"Gemini embedding generation failed: {str(e)}") from e

        return all_embeddings


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory function instantiating active GeminiEmbeddingProvider.
    """
    return GeminiEmbeddingProvider()
