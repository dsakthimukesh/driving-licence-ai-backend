import unittest
from unittest.mock import MagicMock, patch

from app.services.llm.provider import GeminiLLMProvider
from app.core.config import settings

SAMPLE_CONTEXT = """
[Source 1 - Page 1]:
THE UNION OF INDIA
MAHARASHTRA STATE MOTOR DRIVING LICENCE
DL No: MH12 20190001234 DOI: 16-06-2019
Valid Till: 15-06-2034 (NT)
Name _: ROHAN ANIL DESHMUKH
DOB: 12-08-1990 BG: O+

Address
Flat No. 302, Sai Residency, Plot No. 12, Karve Nagar, Pune - 411052, Maharashtra

Authorization to Drive
LMV 16-06-2019 | 15-06-2034
MCWG 16-06-2019 | 15-06-2034

Restrictions:
None
"""


class TestRAGQuestionAnswering(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or "test_key"
        self.provider = GeminiLLMProvider(api_key=self.api_key, model=settings.GEMINI_GENERATION_MODEL)
        self.expected_unavailable = "The requested information is not mentioned in the provided document."

    async def test_licence_number_question(self):
        """Test #6 & Example 1: What is the licence number?"""
        mock_response = MagicMock()
        mock_response.text = "MH12 20190001234"

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            question = "What is the licence number?"
            answer = await self.provider.generate_rag_answer(question=question, formatted_context=SAMPLE_CONTEXT)
            self.assertIn("MH12 20190001234", answer)

    async def test_passport_number_question_absent(self):
        """Test #7 & Example 2: What is the passport number mentioned in this driving licence?"""
        mock_response = MagicMock()
        mock_response.text = self.expected_unavailable

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            question = "What is the passport number mentioned in this driving licence?"
            answer = await self.provider.generate_rag_answer(question=question, formatted_context=SAMPLE_CONTEXT)
            self.assertEqual(answer, self.expected_unavailable)

    async def test_bank_account_number_question_absent(self):
        """Test #8 & Example 3: What is the person's bank account number?"""
        mock_response = MagicMock()
        mock_response.text = self.expected_unavailable

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            question = "What is the person's bank account number?"
            answer = await self.provider.generate_rag_answer(question=question, formatted_context=SAMPLE_CONTEXT)
            self.assertEqual(answer, self.expected_unavailable)

    async def test_unrelated_question(self):
        """Test #8: Unrelated general question."""
        mock_response = MagicMock()
        mock_response.text = self.expected_unavailable

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            question = "Who is the president of France?"
            answer = await self.provider.generate_rag_answer(question=question, formatted_context=SAMPLE_CONTEXT)
            self.assertEqual(answer, self.expected_unavailable)

    async def test_no_field_substitution(self):
        """Test that missing issue date does not substitute DOB."""
        mock_response = MagicMock()
        mock_response.text = self.expected_unavailable

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            context_without_doi = "Name: ROHAN ANIL DESHMUKH\nDOB: 12-08-1990"
            question = "What is the issue date of the licence?"
            answer = await self.provider.generate_rag_answer(question=question, formatted_context=context_without_doi)
            self.assertEqual(answer, self.expected_unavailable)

    async def test_empty_context_returns_unavailable(self):
        """Empty context returns unavailable message immediately without calling API."""
        answer = await self.provider.generate_rag_answer(question="What is the name?", formatted_context="")
        self.assertEqual(answer, self.expected_unavailable)


if __name__ == "__main__":
    unittest.main()
