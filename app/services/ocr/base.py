import uuid
from abc import ABC, abstractmethod
from app.services.ocr.models import OCRResult


class BaseOCRProvider(ABC):
    """
    Abstract Base Class defining the OCR Provider Interface.
    Allows easy swapping between cloud OCR engines (e.g. AWS Textract, Google Vision)
    and local fallback/development providers.
    """

    @abstractmethod
    async def extract_text(
        self,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
        document_id: uuid.UUID
    ) -> OCRResult:
        """
        Extracts raw text from file bytes and returns a structured OCRResult model.
        """
        pass
