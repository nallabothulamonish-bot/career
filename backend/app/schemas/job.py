from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: list[str] = []
    job_type: str = "Full-Time"
    location: str = "On-Campus"
    ctc_or_stipend: str = ""
    min_cgpa: float = 0.0
    eligible_branches: list[str] = []
    application_deadline: datetime


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    ctc_or_stipend: Optional[str] = None
    min_cgpa: Optional[float] = None
    eligible_branches: Optional[list[str]] = None
    application_deadline: Optional[datetime] = None
    status: Optional[str] = None


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    description: str
    required_skills: list
    job_type: str
    location: str
    ctc_or_stipend: str
    min_cgpa: float
    eligible_branches: list
    application_deadline: datetime
    posted_by: int
    status: str

    class Config:
        from_attributes = True
