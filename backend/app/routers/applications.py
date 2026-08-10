from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.application import Application, ApplicationStatus
from app.models.student_profile import StudentProfile
from app.schemas.application import ApplicationStatusUpdate, ApplicationOut
from app.core.deps import require_role
from app.services.resume_matcher import match_resume_to_job

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/{job_id}/apply")
def apply_to_job(job_id: int, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.open:
        raise HTTPException(status_code=400, detail="This drive is closed")

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile before applying")
    if profile.cgpa < job.min_cgpa:
        raise HTTPException(status_code=400, detail=f"Minimum CGPA required is {job.min_cgpa}")
    if job.eligible_branches and profile.branch not in job.eligible_branches:
        raise HTTPException(status_code=400, detail="Your branch is not eligible for this drive")

    existing = db.query(Application).filter(Application.job_id == job_id, Application.student_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already applied to this job")

    match = match_resume_to_job(profile.resume_text, profile.skills or [], job.description, job.required_skills or [])

    application = Application(
        job_id=job.id,
        student_id=user.id,
        match_score=match["score"],
        matched_skills=match["matched_skills"],
        missing_skills=match["missing_skills"],
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {"application": ApplicationOut.model_validate(application), "match_details": match}


@router.get("/mine", response_model=list[dict])
def my_applications(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    apps = db.query(Application).filter(Application.student_id == user.id).order_by(Application.created_at.desc()).all()
    result = []
    for a in apps:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        result.append({
            **ApplicationOut.model_validate(a).model_dump(),
            "job": {"id": job.id, "title": job.title, "company": job.company} if job else None,
        })
    return result


@router.get("/job/{job_id}", response_model=list[dict])
def applicants_for_job(job_id: int, user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    apps = db.query(Application).filter(Application.job_id == job_id).order_by(Application.match_score.desc()).all()
    result = []
    for a in apps:
        student = db.query(User).filter(User.id == a.student_id).first()
        result.append({
            **ApplicationOut.model_validate(a).model_dump(),
            "student": {"id": student.id, "name": student.name, "email": student.email} if student else None,
        })
    return result


@router.put("/{app_id}/status", response_model=dict)
def update_application_status(app_id: int, payload: ApplicationStatusUpdate, user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.status:
        application.status = ApplicationStatus(payload.status)
    if payload.officer_notes is not None:
        application.officer_notes = payload.officer_notes

    if payload.status == "Selected":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == application.student_id).first()
        if profile:
            profile.placed = True

    db.commit()
    db.refresh(application)
    student = db.query(User).filter(User.id == application.student_id).first()
    return {
        **ApplicationOut.model_validate(application).model_dump(),
        "student": {"id": student.id, "name": student.name, "email": student.email} if student else None,
    }


@router.get("/analytics")
def analytics(user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    total_students = db.query(StudentProfile).count()
    placed_students = db.query(StudentProfile).filter(StudentProfile.placed == True).count()  # noqa: E712
    total_jobs = db.query(Job).count()
    open_jobs = db.query(Job).filter(Job.status == JobStatus.open).count()
    total_applications = db.query(Application).count()

    status_rows = db.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    status_breakdown = [{"status": s.value, "count": c} for s, c in status_rows]

    avg_score = db.query(func.avg(Application.match_score)).scalar() or 0

    return {
        "total_students": total_students,
        "placed_students": placed_students,
        "placement_rate": round((placed_students / total_students) * 100) if total_students else 0,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "total_applications": total_applications,
        "avg_match_score": round(float(avg_score), 1),
        "status_breakdown": status_breakdown,
    }
