from pydantic import BaseModel
from datetime import datetime


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str
    target_job_title: str = ""
    target_job_description: str = ""


class ResumeAnalysisOut(BaseModel):
    ats_score: float
    keyword_score: float
    readability_score: float
    structure_score: float
    strengths: list[str]
    suggestions: list[str]
    detected_skills: list[str]
