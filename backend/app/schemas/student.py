from pydantic import BaseModel
from typing import Optional


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[int] = None
    percentage: Optional[float] = None


class StudentProfileUpdate(BaseModel):
    roll_number: Optional[str] = None
    branch: Optional[str] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    phone: Optional[str] = None
    skills: Optional[list[str]] = None
    resume_text: Optional[str] = None
    resume_filename: Optional[str] = None
    education: Optional[list[EducationItem]] = None


class StudentProfileOut(BaseModel):
    id: int
    user_id: int
    roll_number: str
    branch: str
    cgpa: float
    graduation_year: Optional[int]
    phone: str
    skills: list
    resume_text: str
    resume_filename: str
    education: list
    placed: bool

    class Config:
        from_attributes = True
