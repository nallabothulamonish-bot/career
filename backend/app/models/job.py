from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey, DateTime, Enum, Boolean, UniqueConstraint, Index, func
import enum
from datetime import datetime, timezone

from app.db.database import Base


class JobStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Production Job Sync Fields
    source = Column(String(50), nullable=False, default="manual")  # e.g., "greenhouse", "lever", "manual"
    source_job_id = Column(String(100), nullable=False, default="")  # ID assigned by external ATS
    company = Column(String(150), nullable=False, index=True)
    title = Column(String(150), nullable=False, index=True)
    location = Column(String(150), nullable=False, default="Remote", index=True)
    job_type = Column(String(50), nullable=False, default="Full-Time", index=True)  # Full-Time, Internship, Contract
    description = Column(Text, nullable=False, default="")
    requirements = Column(Text, nullable=False, default="")
    skills = Column(JSON, default=list)  # list of skill keywords e.g. ["Python", "React"]
    application_url = Column(String(500), nullable=False, default="")
    
    posted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now())

    is_active = Column(Boolean, default=True, index=True)
    is_remote = Column(Boolean, default=False, index=True)

    # Legacy & Campus Specific Compatibility Fields
    required_skills = Column(JSON, default=list)
    ctc_or_stipend = Column(String(50), default="")
    min_cgpa = Column(Float, default=0.0)
    eligible_branches = Column(JSON, default=list)
    posted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.open)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uix_source_source_job_id"),
        Index("idx_company_active", "company", "is_active"),
        Index("idx_location_remote", "location", "is_remote"),
        Index("idx_active_posted", "is_active", "posted_at"),
    )
