from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: str
    category: str
    question: str
    code_snippet: Optional[str] = None
    options: List[str]


class StartTestRequest(BaseModel):
    category: str
    num_questions: int = Field(default=5, ge=1, le=10)


class TestSubmissionAnswer(BaseModel):
    question_id: str
    selected_option: int  # 0-indexed index of selected option


class SubmitTestRequest(BaseModel):
    category: str
    answers: List[TestSubmissionAnswer]


class QuestionFeedback(BaseModel):
    question_id: str
    question: str
    code_snippet: Optional[str] = None
    options: List[str]
    user_selected: int
    correct_option: int
    is_correct: bool
    explanation: str


class SubmitTestResponse(BaseModel):
    category: str
    score_percentage: float
    total_questions: int
    correct_answers: int
    feedback: List[QuestionFeedback]
    performance_summary: str
