from app.services.ocr.models import OCRPageResult, OCRResult
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.provider import AWSTextractOCRProvider, LocalFallbackOCRProvider, get_ocr_provider

__all__ = [
    "OCRPageResult",
    "OCRResult",
    "BaseOCRProvider",
    "AWSTextractOCRProvider",
    "LocalFallbackOCRProvider",
    "get_ocr_provider"
]
