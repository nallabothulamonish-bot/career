from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class JobSummaryOut(BaseModel):
    id: int
    company: str
    title: str
    location: str
    job_type: str
    match_score: Optional[float] = None
    application_url: str
    source: str


class ChatResponse(BaseModel):
    message: str
    intent: str
    jobs: List[JobSummaryOut] = []
    suggestions: List[str] = []
    session_id: str
