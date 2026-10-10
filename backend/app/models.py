from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CertificateStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=False)
    date = Column(String(50), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    total_recipients = Column(Integer, default=0)
    succeeded_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String(100), unique=True, nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    status = Column(Enum(CertificateStatus), default=CertificateStatus.PENDING)
    error_message = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="certificates")
