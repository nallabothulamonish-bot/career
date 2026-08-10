from sqlalchemy import Column, Integer, Float, String, Text, JSON, ForeignKey, DateTime, Enum, UniqueConstraint, func
import enum

from app.db.database import Base


class ApplicationStatus(str, enum.Enum):
    Applied = "Applied"
    Shortlisted = "Shortlisted"
    Interview = "Interview"
    Selected = "Selected"
    Rejected = "Rejected"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "student_id", name="uq_job_student"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Float, default=0.0)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.Applied)
    officer_notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
