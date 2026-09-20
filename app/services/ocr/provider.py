import io
import os
import shutil
import logging
import time
import uuid
from typing import List, Optional
import boto3
from PIL import Image
import pypdf
import pytesseract

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.models import OCRResult, OCRPageResult

logger = logging.getLogger(__name__)


def resolve_tesseract_cmd() -> Optional[str]:
    """
    Resolves and validates the Tesseract OCR executable path.
    Checks:
    1. Configured TESSERACT_CMD setting if file exists.
    2. System PATH via shutil.which("tesseract").
    3. Common Windows & Linux installation paths.
    """
    if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
        return settings.TESSERACT_CMD

    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        return tesseract_in_path

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


class AWSTextractOCRProvider(BaseOCRProvider):
    """
    AWS Textract OCR Provider.
    Uses AWS boto3 client to extract document text via Textract API.
    """

    def __init__(self):
        kwargs = {}
        if settings.AWS_REGION:
            kwargs["region_name"] = settings.AWS_REGION
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.client = boto3.client("textract", **kwargs)

    async def extract_text(
        self,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
        document_id: uuid.UUID
    ) -> OCRResult:
        start_time = time.time()

        try:
            response = self.client.detect_document_text(
                Document={"Bytes": file_bytes}
            )
            
            blocks = response.get("Blocks", [])
            lines: List[str] = []
            
            for block in blocks:
                if block.get("BlockType") == "LINE":
                    lines.append(block.get("Text", ""))

            full_text = "\n".join(lines)
            pages = [OCRPageResult(page_number=1, text=full_text)]
            elapsed_ms = int((time.time() - start_time) * 1000)

            return OCRResult(
                document_id=document_id,
                provider="aws_textract",
                text=full_text,
                pages=pages,
                processing_time_ms=elapsed_ms
            )
        except Exception as e:
            logger.error(f"AWS Textract OCR failed for document '{document_id}': {str(e)}")
            raise e


class LocalFallbackOCRProvider(BaseOCRProvider):
    """
    Genuine local OCR Provider powered by Tesseract OCR (pytesseract) and pypdf.
    Performs actual text extraction for PNG, JPG, JPEG images and PDF documents.
    """

    def __init__(self):
        cmd = resolve_tesseract_cmd()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
            logger.info(f"LocalFallbackOCRProvider initialized with Tesseract binary at: {cmd}")
        else:
            logger.warning(
                "Tesseract executable not found during initialization. "
                "Image OCR text extraction will raise DocumentProcessingError until Tesseract is installed."
            )

    def _ensure_tesseract_available(self) -> str:
        cmd = resolve_tesseract_cmd()
        if not cmd:
            err_msg = (
                "Tesseract OCR executable is not installed or not found. "
                "Please install Tesseract OCR on Windows (e.g., 'winget install UB-Mannheim.TesseractOCR' "
                "or download setup from https://github.com/UB-Mannheim/tesseract/wiki) "
                "and ensure TESSERACT_CMD path is set in settings."
            )
            logger.error(err_msg)
            raise DocumentProcessingError(err_msg)
        pytesseract.pytesseract.tesseract_cmd = cmd
        return cmd

    async def extract_text(
        self,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
        document_id: uuid.UUID
    ) -> OCRResult:
        start_time = time.time()

        if not file_bytes:
            raise ValueError("File content is empty (0 bytes).")

        clean_mime = mime_type.lower()
        is_pdf = "pdf" in clean_mime or file_name.lower().endswith(".pdf")

        if is_pdf:
            pages = await self._process_pdf(file_bytes, file_name)
        else:
            pages = await self._process_image(file_bytes, file_name)

        combined_text = "\n\n".join([p.text for p in pages if p.text]).strip()

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Local OCR completed for doc_id='{document_id}' (file='{file_name}'): "
            f"pages={len(pages)}, char_count={len(combined_text)}, time_ms={elapsed_ms}"
        )

        return OCRResult(
            document_id=document_id,
            provider="local_fallback",
            text=combined_text,
            pages=pages,
            processing_time_ms=elapsed_ms
        )

    async def _process_image(self, file_bytes: bytes, file_name: str) -> List[OCRPageResult]:
        self._ensure_tesseract_available()
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert palette/RGBA images to RGB for pytesseract compatibility
            if image.mode in ("RGBA", "P", "LA"):
                image = image.convert("RGB")

            extracted_text = pytesseract.image_to_string(image).strip()
            return [OCRPageResult(page_number=1, text=extracted_text)]
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Pytesseract extraction failed for image '{file_name}': {e}")
            raise DocumentProcessingError(f"Tesseract OCR failed to extract text from image '{file_name}': {str(e)}") from e

    async def _process_pdf(self, file_bytes: bytes, file_name: str) -> List[OCRPageResult]:
        pages: List[OCRPageResult] = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for idx, page in enumerate(reader.pages, start=1):
                extracted_page_text = (page.extract_text() or "").strip()

                if extracted_page_text:
                    pages.append(OCRPageResult(page_number=idx, text=extracted_page_text))
                else:
                    # Scanned PDF page: attempt OCR on page images if present
                    ocr_page_text = ""
                    try:
                        self._ensure_tesseract_available()
                        for img_obj in page.images:
                            img = Image.open(io.BytesIO(img_obj.data))
                            if img.mode in ("RGBA", "P", "LA"):
                                img = img.convert("RGB")
                            txt = pytesseract.image_to_string(img).strip()
                            if txt:
                                ocr_page_text += txt + "\n"
                    except Exception as ocr_err:
                        logger.warning(f"PDF page {idx} image OCR fallback skipped/failed: {ocr_err}")

                    pages.append(OCRPageResult(page_number=idx, text=ocr_page_text.strip()))
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"PDF extraction failed for file '{file_name}': {e}")
            raise DocumentProcessingError(f"Failed to process PDF document '{file_name}': {str(e)}") from e

        return pages


def get_ocr_provider() -> BaseOCRProvider:
    """
    Factory function for instantiating the appropriate OCR Provider based on configuration.
    """
    provider_mode = settings.OCR_PROVIDER.strip().lower()

    if provider_mode == "aws_textract":
        return AWSTextractOCRProvider()
    elif provider_mode == "auto":
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                return AWSTextractOCRProvider()
            except Exception as e:
                logger.warning(f"Failed to initialize AWS Textract provider, falling back to Local: {e}")
                return LocalFallbackOCRProvider()
        return LocalFallbackOCRProvider()
    else:
        return LocalFallbackOCRProvider()

