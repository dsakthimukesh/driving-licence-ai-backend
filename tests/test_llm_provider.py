import json
import logging
import unittest
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm.provider import (
    GeminiLLMProvider,
    GroqLLMProvider,
    FallbackLLMProvider,
    get_llm_provider
)
from app.services.llm.schemas import DrivingLicenceExtractionSchema
from app.core.config import settings

EXACT_TEST_OCR_TEXT = """MAHARASHTRA STATE MOTOR DRIVING LICENCE
Licence No: MH1220110012345  DOI: 16-06-2019
Name: ROHAN ANIL DESHMUKH
Father's Name: ANIL VASANT DESHMUKH
DOB: 12-08-1990  BG: O+
Address: Flat No. 302, Sai Residency, Plot No. 12, Karve Nagar, Pune - 411052
Restrictions: None
COV: LMV, MCWG
Issuing Authority: RTO Pune"""


class TestGeminiLLMProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.doc_id = uuid.uuid4()
        self.api_key = settings.GOOGLE_API_KEY or "test_api_key"
        self.provider = GeminiLLMProvider(api_key=self.api_key, model=settings.GEMINI_GENERATION_MODEL)

    async def test_missing_api_key(self):
        """Test Calling provider without API key raises ValueError."""
        no_key_provider = GeminiLLMProvider(api_key="")
        with self.assertRaises(ValueError) as ctx:
            await no_key_provider.extract_info(ocr_text=EXACT_TEST_OCR_TEXT, document_id=self.doc_id)
        self.assertIn("Google Gemini API key is missing", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            await no_key_provider.generate_rag_answer(question="Test?", formatted_context="Context")
        self.assertIn("Google Gemini API key is missing", str(ctx.exception))

    async def test_gemini_extraction_valid_ocr_text(self):
        """Test Gemini extraction with valid OCR text."""
        expected_json = {
            "licence_number": "MH1220110012345",
            "full_name": "ROHAN ANIL DESHMUKH",
            "parent_name": "ANIL VASANT DESHMUKH",
            "date_of_birth": "1990-08-12",
            "blood_group": "O+",
            "address": "Flat No. 302, Sai Residency, Plot No. 12, Karve Nagar, Pune - 411052",
            "issue_date": "2019-06-16",
            "expiry_date": None,
            "vehicle_authorization": "LMV, MCWG",
            "issuing_authority": "RTO Pune",
            "restrictions": "None",
            "other_information": None
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(expected_json)

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            result: DrivingLicenceExtractionSchema = await self.provider.extract_info(
                ocr_text=EXACT_TEST_OCR_TEXT,
                document_id=self.doc_id
            )

            self.assertIsInstance(result, DrivingLicenceExtractionSchema)
            self.assertEqual(result.full_name, "ROHAN ANIL DESHMUKH")
            self.assertEqual(result.parent_name, "ANIL VASANT DESHMUKH")
            self.assertEqual(result.date_of_birth, date(1990, 8, 12))
            self.assertEqual(result.blood_group, "O+")
            self.assertIn("Pune", result.address or "")
            self.assertEqual(result.licence_number, "MH1220110012345")

    async def test_gemini_extraction_missing_fields(self):
        """Test missing driving licence fields return null without inventing values."""
        partial_json = {
            "licence_number": None,
            "full_name": "ROHAN ANIL DESHMUKH",
            "parent_name": None,
            "date_of_birth": "1990-08-12",
            "blood_group": None,
            "address": "Pune, Maharashtra",
            "issue_date": None,
            "expiry_date": None,
            "vehicle_authorization": None,
            "issuing_authority": None,
            "restrictions": None,
            "other_information": None
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(partial_json)

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            result: DrivingLicenceExtractionSchema = await self.provider.extract_info(
                ocr_text="Name: ROHAN ANIL DESHMUKH\nDOB: 12-08-1990",
                document_id=self.doc_id
            )

            self.assertEqual(result.full_name, "ROHAN ANIL DESHMUKH")
            self.assertEqual(result.date_of_birth, date(1990, 8, 12))
            self.assertIsNone(result.licence_number)
            self.assertIsNone(result.parent_name)

    async def test_invalid_gemini_response(self):
        """Test invalid or malformed Gemini response handling."""
        mock_response = MagicMock()
        mock_response.text = "NOT_A_VALID_JSON_STRING"

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            with self.assertRaises(ValueError) as ctx:
                await self.provider.extract_info(ocr_text="test ocr", document_id=self.doc_id)
            self.assertIn("Invalid or malformed Gemini response JSON", str(ctx.exception))

    async def test_verbose_blood_group_and_long_fields(self):
        """Test extraction with verbose blood group descriptions and long RTO authority names."""
        verbose_json = {
            "licence_number": "MH12 20190001234",
            "full_name": "ROHAN ANIL DESHMUKH",
            "parent_name": "ANIL VASANT DESHMUKH",
            "date_of_birth": "1990-08-12",
            "blood_group": "O legally O positive",
            "address": "Flat No. 302, Sai Residency, Plot No. 12, Karve Nagar, Pune - 411052, Maharashtra",
            "issue_date": "2019-06-16",
            "expiry_date": "2034-06-15",
            "vehicle_authorization": "LMV, MCWG",
            "issuing_authority": "REGIONAL TRANSPORT OFFICE, PUNE DIVISION, MAHARASHTRA STATE, INDIA",
            "restrictions": "None",
            "other_information": "(NT) ule 16 (2)"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(verbose_json)

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            result: DrivingLicenceExtractionSchema = await self.provider.extract_info(
                ocr_text="test ocr text",
                document_id=self.doc_id
            )

            self.assertEqual(result.blood_group, "O legally O positive")
            self.assertEqual(result.issuing_authority, "REGIONAL TRANSPORT OFFICE, PUNE DIVISION, MAHARASHTRA STATE, INDIA")


class TestFallbackLLMProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.doc_id = uuid.uuid4()
        self.mock_gemini = AsyncMock(spec=GeminiLLMProvider)
        self.mock_gemini.model = "gemini-3.6-flash"
        self.mock_groq = AsyncMock(spec=GroqLLMProvider)
        self.mock_groq.model = "openai/gpt-oss-120b"
        self.orchestrator = FallbackLLMProvider(
            primary_provider=self.mock_gemini,
            fallback_provider=self.mock_groq
        )

    async def test_gemini_primary_success(self):
        """Test #1: Gemini primary succeeds without calling fallback."""
        expected_schema = DrivingLicenceExtractionSchema(
            licence_number="MH1220110012345",
            full_name="ROHAN ANIL DESHMUKH"
        )
        self.mock_gemini.extract_info.return_value = expected_schema

        result = await self.orchestrator.extract_info(EXACT_TEST_OCR_TEXT, self.doc_id)

        self.assertEqual(result.licence_number, "MH1220110012345")
        self.mock_gemini.extract_info.assert_called_once_with(ocr_text=EXACT_TEST_OCR_TEXT, document_id=self.doc_id)
        self.mock_groq.extract_info.assert_not_called()

    async def test_gemini_503_fallback_success(self):
        """Test #2: Gemini 503 error triggers fallback provider success."""
        self.mock_gemini.extract_info.side_effect = RuntimeError("Gemini 503 UNAVAILABLE: high demand")
        expected_schema = DrivingLicenceExtractionSchema(
            licence_number="MH1220110012345",
            full_name="ROHAN ANIL DESHMUKH (Fallback)"
        )
        self.mock_groq.extract_info.return_value = expected_schema

        result = await self.orchestrator.extract_info(EXACT_TEST_OCR_TEXT, self.doc_id)

        self.assertEqual(result.full_name, "ROHAN ANIL DESHMUKH (Fallback)")
        self.mock_gemini.extract_info.assert_called_once()
        self.mock_groq.extract_info.assert_called_once_with(ocr_text=EXACT_TEST_OCR_TEXT, document_id=self.doc_id)

    async def test_gemini_quota_429_fallback_success(self):
        """Test #3: Gemini 429 daily quota exhaustion immediately triggers fallback success."""
        self.mock_gemini.extract_info.side_effect = RuntimeError("Gemini API error 429: DAILY_QUOTA_EXCEEDED")
        expected_schema = DrivingLicenceExtractionSchema(
            licence_number="MH1220110012345",
            full_name="ROHAN ANIL DESHMUKH (Quota Fallback)"
        )
        self.mock_groq.extract_info.return_value = expected_schema

        result = await self.orchestrator.extract_info(EXACT_TEST_OCR_TEXT, self.doc_id)

        self.assertEqual(result.full_name, "ROHAN ANIL DESHMUKH (Quota Fallback)")
        self.mock_gemini.extract_info.assert_called_once()
        self.mock_groq.extract_info.assert_called_once()

    async def test_both_providers_failing(self):
        """Test #4: Both primary and fallback providers fail, raising RuntimeError."""
        self.mock_gemini.extract_info.side_effect = RuntimeError("Gemini Service Unavailable")
        self.mock_groq.extract_info.side_effect = RuntimeError("Groq Rate Limit Exceeded")

        with self.assertRaises(RuntimeError) as ctx:
            await self.orchestrator.extract_info(EXACT_TEST_OCR_TEXT, self.doc_id)

        self.assertIn("All AI LLM providers unavailable", str(ctx.exception))

    async def test_schema_validation_failure(self):
        """Test #5: Schema validation failure in provider returns ValueError."""
        groq_provider = GroqLLMProvider(api_key="gsk_fake_test_key")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "INVALID_JSON_PAYLOAD"}}]
            }
            mock_post.return_value = mock_resp

            with self.assertRaises(ValueError) as ctx:
                await groq_provider.extract_info(EXACT_TEST_OCR_TEXT, self.doc_id)

            self.assertIn("Invalid or malformed Groq response JSON", str(ctx.exception))

    async def test_no_api_key_leakage_in_logs(self):
        """Test #6: Logging contains metadata (provider name, model name, doc ID) but NEVER leaks API keys."""
        secret_gemini_key = "AIzaSySecretGeminiKey123456789"
        secret_groq_key = "gsk_SecretGroqKey987654321"

        gemini = GeminiLLMProvider(api_key=secret_gemini_key)
        groq = GroqLLMProvider(api_key=secret_groq_key)
        orchestrator = FallbackLLMProvider(primary_provider=gemini, fallback_provider=groq)

        with patch.object(gemini, "extract_info", side_effect=RuntimeError("Gemini 503 Service Unavailable")), \
             patch.object(groq, "extract_info", return_value=DrivingLicenceExtractionSchema(full_name="Safe Log Test")), \
             self.assertLogs("app.services.llm.provider", level="INFO") as log_cm:

            await orchestrator.extract_info("test ocr", self.doc_id)

            all_log_output = "\n".join(log_cm.output)

            # Assert metadata presence
            self.assertIn("GeminiLLMProvider", all_log_output)
            self.assertIn("GroqLLMProvider", all_log_output)
            self.assertIn(str(self.doc_id), all_log_output)
            self.assertIn("Step 3/8", all_log_output)

            # Assert NO API Key leakage
            self.assertNotIn(secret_gemini_key, all_log_output)
            self.assertNotIn(secret_groq_key, all_log_output)


if __name__ == "__main__":
    unittest.main()
