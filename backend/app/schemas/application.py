from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ApplicationStatusUpdate(BaseModel):
    status: Optional[str] = None
    officer_notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    student_id: int
    match_score: float
    matched_skills: list
    missing_skills: list
    status: str
    officer_notes: str
    created_at: datetime

    class Config:
        from_attributes = True
