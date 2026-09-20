import uuid
from abc import ABC, abstractmethod
from app.services.llm.schemas import DrivingLicenceExtractionSchema


class BaseLLMProvider(ABC):
    """
    Abstract Base Class defining the LLM Extraction Provider interface.
    Enables structured extraction and grounded RAG answer generation.
    """

    @abstractmethod
    async def extract_info(
        self,
        ocr_text: str,
        document_id: uuid.UUID
    ) -> DrivingLicenceExtractionSchema:
        """
        Processes raw OCR text and extracts structured driving licence fields.
        """
        pass

    @abstractmethod
    async def generate_rag_answer(
        self,
        question: str,
        formatted_context: str
    ) -> str:
        """
        Generates a grounded natural language answer to a question based strictly on formatted retrieved context.
        """
        pass
