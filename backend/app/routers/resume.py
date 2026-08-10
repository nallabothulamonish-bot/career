import io
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from pypdf import PdfReader
import docx

from app.db.database import get_db
from app.models.user import User
from app.models.resume_analysis import ResumeAnalysis
from app.schemas.resume import ResumeAnalyzeRequest, ResumeAnalysisOut
from app.core.deps import require_role
from app.services.resume_analyzer import analyze_resume

router = APIRouter(prefix="/api/resume", tags=["resume"])


def extract_text_from_file(file_filename: str, file_bytes: bytes) -> str:
    filename_lower = file_filename.lower()
    if filename_lower.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read PDF file: {str(e)}")
    elif filename_lower.endswith(".docx") or filename_lower.endswith(".doc"):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs if para.text])
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read Word document: {str(e)}")
    else:
        try:
            return file_bytes.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read text file: {str(e)}")


@router.post("/analyze", response_model=ResumeAnalysisOut)
def analyze(payload: ResumeAnalyzeRequest, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    result = analyze_resume(payload.resume_text, payload.target_job_title, payload.target_job_description)

    record = ResumeAnalysis(
        student_id=user.id,
        ats_score=result["ats_score"],
        keyword_score=result["keyword_score"],
        readability_score=result["readability_score"],
        structure_score=result["structure_score"],
        strengths=result["strengths"],
        suggestions=result["suggestions"],
        detected_skills=result["detected_skills"],
        target_role={"title": payload.target_job_title, "description": payload.target_job_description[:500]},
    )
    db.add(record)
    db.commit()

    return ResumeAnalysisOut(**result)


@router.post("/upload-and-analyze", response_model=ResumeAnalysisOut)
async def upload_and_analyze(
    file: UploadFile = File(...),
    target_job_title: Optional[str] = Form(""),
    target_job_description: Optional[str] = Form(""),
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_name = file.filename or "resume.txt"
    resume_text = extract_text_from_file(file_name, contents)
    if not resume_text or len(resume_text) < 30:
        raise HTTPException(
            status_code=400,
            detail="Could not extract sufficient text from the uploaded document. Please ensure it contains readable text.",
        )

    result = analyze_resume(resume_text, target_job_title or "", target_job_description or "")

    record = ResumeAnalysis(
        student_id=user.id,
        ats_score=result["ats_score"],
        keyword_score=result["keyword_score"],
        readability_score=result["readability_score"],
        structure_score=result["structure_score"],
        strengths=result["strengths"],
        suggestions=result["suggestions"],
        detected_skills=result["detected_skills"],
        target_role={"title": target_job_title, "description": (target_job_description or "")[:500]},
    )
    db.add(record)
    db.commit()

    return ResumeAnalysisOut(**result)


@router.get("/history", response_model=list[dict])
def history(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    records = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.student_id == user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": r.id,
            "ats_score": r.ats_score,
            "keyword_score": r.keyword_score,
            "readability_score": r.readability_score,
            "structure_score": r.structure_score,
            "target_role": r.target_role,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

