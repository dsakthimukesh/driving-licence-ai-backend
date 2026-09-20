import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class DrivingLicenceExtractionSchema(BaseModel):
    """
    Structured extraction schema for Indian Driving Licences.
    Contains all 12 fields matching public.document_info columns.
    """
    licence_number: Optional[str] = Field(
        default=None,
        description="Unique driving licence number (e.g. DL-1420110012345, MH1220110012345)."
    )
    full_name: Optional[str] = Field(
        default=None,
        description="Full name of the licence holder."
    )
    parent_name: Optional[str] = Field(
        default=None,
        description="Father's, Mother's, or Spouse's name."
    )
    date_of_birth: Optional[date] = Field(
        default=None,
        description="Date of birth formatted as YYYY-MM-DD or None if missing."
    )
    blood_group: Optional[str] = Field(
        default=None,
        description="Blood group (e.g. O+, A+, B+, AB-, etc.)."
    )
    address: Optional[str] = Field(
        default=None,
        description="Full residential address."
    )
    issue_date: Optional[date] = Field(
        default=None,
        description="Licence issue date formatted as YYYY-MM-DD or None."
    )
    expiry_date: Optional[date] = Field(
        default=None,
        description="Licence expiration date formatted as YYYY-MM-DD or None."
    )
    vehicle_authorization: Optional[str] = Field(
        default=None,
        description="Vehicle classes authorized to drive (e.g., LMV, MCWG, TRANS)."
    )
    issuing_authority: Optional[str] = Field(
        default=None,
        description="Name or office location of issuing RTO authority."
    )
    restrictions: Optional[str] = Field(
        default=None,
        description="Specific restrictions or driver conditions."
    )
    other_information: Optional[str] = Field(
        default=None,
        description="Extra notes, unparsed details, or unverified text."
    )


class LLMExtractionResult(BaseModel):
    """
    Container for complete LLM extraction metadata and structured data payload.
    """
    document_id: uuid.UUID
    provider: str
    model: str
    data: DrivingLicenceExtractionSchema
    raw_response: Optional[str] = None
