import unittest
from unittest.mock import MagicMock, patch
from google.genai import errors

from app.services.embeddings.provider import GeminiEmbeddingProvider, get_embedding_provider
from app.core.config import settings


class TestGeminiEmbeddingProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or "test_key"
        self.provider = GeminiEmbeddingProvider(api_key=self.api_key)

    async def test_missing_gemini_api_key(self):
        """Test #10: Missing GEMINI_API_KEY raises ValueError."""
        no_key_provider = GeminiEmbeddingProvider(api_key="")
        with self.assertRaises(ValueError) as ctx:
            await no_key_provider.generate_embeddings(texts=["Hello world"])
        self.assertIn("Google Gemini API key is missing", str(ctx.exception))

    async def test_gemini_document_embeddings(self):
        """Test #2: Gemini document embeddings generation."""
        dummy_vector = [0.1] * 1536
        mock_emb = MagicMock()
        mock_emb.values = dummy_vector
        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb]

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.embed_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            embeddings = await self.provider.generate_embeddings(texts=["Document text chunk"])
            self.assertEqual(len(embeddings), 1)
            self.assertEqual(len(embeddings[0]), 1536)

    async def test_gemini_question_embeddings(self):
        """Test #3: Gemini question embeddings generation."""
        dummy_vector = [0.2] * 1536
        mock_emb = MagicMock()
        mock_emb.values = dummy_vector
        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb]

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.embed_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            embeddings = await self.provider.generate_embeddings(texts=["What is the licence number?"])
            self.assertEqual(len(embeddings), 1)
            self.assertEqual(len(embeddings[0]), 1536)

    async def test_matching_embedding_dimensions(self):
        """Test #4: Generated embedding dimensions strictly match expected database dimension (1536)."""
        self.assertEqual(self.provider.expected_dimensions, 1536)

        # Mismatched dimension from API raises ValueError
        wrong_vector = [0.1] * 768
        mock_emb = MagicMock()
        mock_emb.values = wrong_vector
        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb]

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.embed_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            with self.assertRaises(ValueError) as ctx:
                await self.provider.generate_embeddings(texts=["Test"])
            self.assertIn("Embedding vector dimension mismatch", str(ctx.exception))

    async def test_gemini_api_failure(self):
        """Test #9: Gemini API failure handling."""
        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.embed_content.side_effect = errors.ClientError(
                500, {"error": {"message": "Gemini internal error"}}
            )
            mock_get_client.return_value = mock_client

            with self.assertRaises(RuntimeError) as ctx:
                await self.provider.generate_embeddings(texts=["Test"])
            self.assertIn("Gemini API error during embedding generation", str(ctx.exception))

    async def test_no_openai_fallback(self):
        """Test #11: Provider factory returns GeminiEmbeddingProvider and never OpenAI provider."""
        provider = get_embedding_provider()
        self.assertIsInstance(provider, GeminiEmbeddingProvider)

    async def test_no_synthetic_embeddings(self):
        """Test #12: No synthetic hash-based embeddings or DevelopmentFallbackEmbeddingProvider used."""
        import app.services.embeddings as emb_pkg
        self.assertFalse(hasattr(emb_pkg, "DevelopmentFallbackEmbeddingProvider"))
        self.assertFalse(hasattr(emb_pkg, "OpenAIEmbeddingProvider"))


if __name__ == "__main__":
    unittest.main()
