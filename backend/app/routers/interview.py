import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.db.database import get_db
from app.models.user import User
from app.models.mock_interview import MockInterviewSession, MockInterviewAnswer
from app.schemas.interview import (
    InterviewStartRequest, InterviewStartResponse, InterviewQuestionOut,
    AnswerSubmitRequest, AnswerFeedbackOut, SessionCompleteRequest, SessionResultOut,
)
from app.core.deps import require_role
from app.services.interview_engine import (
    generate_questions, score_answer, summarize_session, get_question_bank_categories,
)

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/categories")
def categories():
    return {"categories": get_question_bank_categories()}


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(payload: InterviewStartRequest, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    session = MockInterviewSession(student_id=user.id, role_category=payload.role_category)
    db.add(session)
    db.commit()
    db.refresh(session)

    questions = generate_questions(payload.role_category, payload.num_questions)
    return InterviewStartResponse(
        session_id=int(session.id),  # type: ignore
        role_category=payload.role_category,


        questions=[
            InterviewQuestionOut(question_id=i, question=q["question"], category=q["category"])
            for i, q in enumerate(questions)
        ],
    )


@router.post("/answer", response_model=AnswerFeedbackOut)
def submit_answer(payload: AnswerSubmitRequest, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == payload.session_id, MockInterviewSession.student_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    result = score_answer(payload.question, payload.answer, payload.category, session.role_category)

    record = MockInterviewAnswer(
        session_id=session.id,
        question=payload.question,
        question_category=payload.category,
        answer=payload.answer,
        score=result["score"],
        feedback=result["feedback"],
    )
    db.add(record)
    db.commit()

    return AnswerFeedbackOut(score=result["score"], feedback=result["feedback"])


@router.post("/complete", response_model=SessionResultOut)
def complete_session(payload: SessionCompleteRequest, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == payload.session_id, MockInterviewSession.student_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    answers = db.query(MockInterviewAnswer).filter(MockInterviewAnswer.session_id == session.id).all()
    answer_dicts = [{"score": a.score, "feedback": a.feedback, "question": a.question} for a in answers]

    overall, summary = summarize_session(answer_dicts)
    session.overall_score = overall
    session.summary = summary
    db.commit()

    return SessionResultOut(
        session_id=session.id,
        overall_score=overall,
        summary=summary,
        answers=[
            {"question": a.question, "answer": a.answer, "score": a.score, "feedback": a.feedback}
            for a in answers
        ],
    )


@router.get("/history")
def interview_history(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    sessions = (
        db.query(MockInterviewSession)
        .filter(MockInterviewSession.student_id == user.id)
        .order_by(MockInterviewSession.created_at.desc())
        .limit(10)
        .all()
    )
    result = []
    for s in sessions:
        answers = db.query(MockInterviewAnswer).filter(MockInterviewAnswer.session_id == s.id).all()
        result.append({
            "id": s.id,
            "role_category": s.role_category,
            "overall_score": s.overall_score,
            "summary": s.summary,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "answers": [
                {
                    "question": a.question,
                    "answer": a.answer,
                    "score": a.score,
                    "feedback": a.feedback or [],
                }
                for a in answers
            ]
        })
    return result

