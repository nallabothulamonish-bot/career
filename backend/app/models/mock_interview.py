from sqlalchemy import Column, Integer, Float, String, Text, JSON, ForeignKey, DateTime, func

from app.db.database import Base


class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_category = Column(String(100), nullable=False)   # e.g. "Software Engineer", "Data Analyst", "HR/Behavioral"
    overall_score = Column(Float, default=0.0)
    summary = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    answers = None  # populated via relationship if needed; kept simple via FK query


class MockInterviewAnswer(Base):
    __tablename__ = "mock_interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("mock_interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    question_category = Column(String(50), default="technical")  # technical | behavioral | hr
    answer = Column(Text, default="")
    score = Column(Float, default=0.0)
    feedback = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
