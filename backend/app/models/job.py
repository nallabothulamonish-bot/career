from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey, DateTime, Enum, func
import enum

from app.db.database import Base


class JobStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    company = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    job_type = Column(String(30), default="Full-Time")
    location = Column(String(100), default="On-Campus")
    ctc_or_stipend = Column(String(50), default="")
    min_cgpa = Column(Float, default=0.0)
    eligible_branches = Column(JSON, default=list)
    application_deadline = Column(DateTime, nullable=False)
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.open)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
