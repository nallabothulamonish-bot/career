from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.assessment import AssessmentResult
from app.schemas.assessment import (
    QuestionOut,
    StartTestRequest,
    SubmitTestRequest,
    SubmitTestResponse,
)
from app.core.deps import require_role
from app.services.assessment_engine import (
    get_available_categories,
    generate_test_questions,
    evaluate_test,
)

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.get("/categories")
def list_categories():
    return {"categories": get_available_categories()}


@router.post("/start", response_model=list[QuestionOut])
def start_test(payload: StartTestRequest, user: User = Depends(require_role("student"))):
    questions = generate_test_questions(payload.category, payload.num_questions)
    return [QuestionOut(**q) for q in questions]


@router.post("/submit", response_model=SubmitTestResponse)
def submit_test(
    payload: SubmitTestRequest,
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    user_answers = [a.model_dump() for a in payload.answers]
    result = evaluate_test(payload.category, user_answers)

    record = AssessmentResult(
        student_id=user.id,
        category=result["category"],
        total_questions=result["total_questions"],
        correct_answers=result["correct_answers"],
        score_percentage=result["score_percentage"],
        details=result["feedback"],
    )
    db.add(record)
    db.commit()

    return SubmitTestResponse(**result)


@router.get("/history", response_model=list[dict])
def get_history(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    records = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.student_id == user.id)
        .order_by(AssessmentResult.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": r.id,
            "category": r.category,
            "score_percentage": r.score_percentage,
            "correct_answers": r.correct_answers,
            "total_questions": r.total_questions,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
