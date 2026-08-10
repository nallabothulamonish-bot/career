import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    placement_officer = "placement_officer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
