from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # e.g., Python, C, C++, Java, Aptitude, Core CS
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)  # question by question results with user answers
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User")

