import json
import unittest
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.llm.provider import GeminiLLMProvider
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
        """Test #7: Calling provider without API key raises ValueError."""
        no_key_provider = GeminiLLMProvider(api_key="")
        with self.assertRaises(ValueError) as ctx:
            await no_key_provider.extract_info(ocr_text=EXACT_TEST_OCR_TEXT, document_id=self.doc_id)
        self.assertIn("Google Gemini API key is missing", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            await no_key_provider.generate_rag_answer(question="Test?", formatted_context="Context")
        self.assertIn("Google Gemini API key is missing", str(ctx.exception))

    async def test_gemini_extraction_valid_ocr_text(self):
        """Test #1: Gemini extraction with valid OCR text."""
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
        """Test #2: Missing driving licence fields return null without inventing values."""
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
            self.assertIsNone(result.issue_date)
            self.assertIsNone(result.expiry_date)

    async def test_invalid_gemini_response(self):
        """Test #6: Invalid or malformed Gemini response handling."""
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
        """Test extraction with verbose blood group descriptions and long RTO authority names without truncation."""
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

    async def test_empty_gemini_response(self):
        """Test handling of empty response from Gemini."""
        mock_response = MagicMock()
        mock_response.text = ""

        with patch.object(self.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            with self.assertRaises(ValueError) as ctx:
                await self.provider.extract_info(ocr_text="test ocr", document_id=self.doc_id)
            self.assertIn("Gemini returned an empty response", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
