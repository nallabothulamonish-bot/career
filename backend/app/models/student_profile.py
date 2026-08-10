from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    roll_number = Column(String(50), default="")
    branch = Column(String(100), default="")
    cgpa = Column(Float, default=0.0)
    graduation_year = Column(Integer, nullable=True)
    phone = Column(String(20), default="")
    skills = Column(JSON, default=list)          # ["python", "react", ...]
    resume_text = Column(Text, default="")        # plain text resume content
    resume_filename = Column(String(255), default="")
    education = Column(JSON, default=list)        # [{degree, institution, year, percentage}]
    placed = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="profile")
