from pydantic import BaseModel
from typing import Optional


class InterviewStartRequest(BaseModel):
    role_category: str  # e.g. "Software Engineer", "Data Analyst", "HR/Behavioral"
    num_questions: int = 5


class InterviewQuestionOut(BaseModel):
    question_id: int
    question: str
    category: str


class InterviewStartResponse(BaseModel):
    session_id: int
    role_category: str
    questions: list[InterviewQuestionOut]


class AnswerSubmitRequest(BaseModel):
    session_id: int
    question_id: int
    question: str
    category: str
    answer: str


class AnswerFeedbackOut(BaseModel):
    score: float
    feedback: list[str]


class SessionCompleteRequest(BaseModel):
    session_id: int


class SessionResultOut(BaseModel):
    session_id: int
    overall_score: float
    summary: str
    answers: list[dict]
