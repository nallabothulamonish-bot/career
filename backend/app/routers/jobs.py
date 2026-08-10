from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobOut
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(status: str | None = Query(None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Job)
    if status:
        q = q.filter(Job.status == JobStatus(status))
    return q.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    job = Job(**payload.model_dump(), posted_by=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.posted_by == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not owned by you")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = JobStatus(data["status"])
    for key, value in data.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, user: User = Depends(require_role("placement_officer")), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.posted_by == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not owned by you")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
