from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, DateTime, func

from app.db.database import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ats_score = Column(Float, default=0.0)
    keyword_score = Column(Float, default=0.0)
    readability_score = Column(Float, default=0.0)
    structure_score = Column(Float, default=0.0)
    strengths = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    detected_skills = Column(JSON, default=list)
    target_role = Column(JSON, default=dict)  # {title, description} if matched against a JD
    created_at = Column(DateTime(timezone=True), server_default=func.now())
