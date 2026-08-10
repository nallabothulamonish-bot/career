from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    requirements: Optional[str] = ""
    skills: List[str] = []
    required_skills: List[str] = []
    job_type: str = "Full-Time"
    location: str = "Remote"
    application_url: Optional[str] = ""
    source: Optional[str] = "manual"
    source_job_id: Optional[str] = ""
    is_remote: bool = False
    ctc_or_stipend: str = ""
    min_cgpa: float = 0.0
    eligible_branches: List[str] = []
    application_deadline: Optional[datetime] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    application_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_remote: Optional[bool] = None
    ctc_or_stipend: Optional[str] = None
    min_cgpa: Optional[float] = None
    eligible_branches: Optional[List[str]] = None
    application_deadline: Optional[datetime] = None
    status: Optional[str] = None


class JobOut(BaseModel):
    id: int
    source: str = "manual"
    source_job_id: str = ""
    company: str
    title: str
    location: str
    job_type: str
    description: str
    requirements: str = ""
    skills: List[str] = []
    required_skills: List[str] = []
    application_url: str = ""
    posted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    is_active: bool = True
    is_remote: bool = False
    
    # Optional dynamic recommendation metadata
    match_score: Optional[float] = None
    match_reasons: Optional[List[str]] = None
    
    # Campus compatibility fields
    ctc_or_stipend: Optional[str] = ""
    min_cgpa: Optional[float] = 0.0
    eligible_branches: Optional[List[str]] = []
    posted_by: Optional[int] = None
    status: Optional[str] = "open"

    class Config:
        from_attributes = True


class PaginatedJobsOut(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    jobs: List[JobOut]
