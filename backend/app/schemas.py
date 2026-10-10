from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CertificateStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr

class JobCreate(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255)
    issuer: str = Field(..., min_length=1, max_length=255)
    date: str = Field(..., min_length=1, max_length=50)
    recipients: List[RecipientCreate] = Field(..., min_items=1, max_items=1000)

    @validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError('recipients list cannot be empty')
        return v

class CertificateResponse(BaseModel):
    certificate_id: str
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: int
    event_name: str
    issuer: str
    date: str
    status: JobStatus
    total_recipients: int
    succeeded_count: int
    failed_count: int
    created_at: datetime
    certificates: List[CertificateResponse]

    class Config:
        from_attributes = True

class JobCreateResponse(BaseModel):
    id: int = Field(alias="id")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {"id": 1}
        }

class VerifyResponse(BaseModel):
    valid: bool
    certificate_id: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    event_name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
