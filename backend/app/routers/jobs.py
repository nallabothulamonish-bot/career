import math
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.db.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.student_profile import StudentProfile
from app.schemas.job import JobCreate, JobUpdate, JobOut, PaginatedJobsOut
from app.core.deps import get_current_user, require_role, get_optional_current_user
from app.services.cache_service import cache_service
from app.services.job_sync import run_job_sync_pipeline
from app.services.recommendation_engine import compute_job_match

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _paginate_query(query, page: int = 1, limit: int = 20) -> tuple[int, int, List[Job]]:
    total = query.count()
    limit = min(max(1, limit), 100)
    page = max(1, page)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    jobs = query.offset(offset).limit(limit).all()
    return total, total_pages, jobs


@router.get("", response_model=PaginatedJobsOut)
def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    skills: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    cache_key = f"jobs:list:p{page}:l{limit}:c{company}:loc{location}:jt{job_type}:r{remote}:s{skills}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    q = db.query(Job).filter(Job.is_active == True)

    if company:
        q = q.filter(func.lower(Job.company) == company.lower())
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        q = q.filter(Job.job_type == job_type)
    if remote is not None:
        q = q.filter(Job.is_remote == remote)
    if skills:
        q = q.filter(Job.description.ilike(f"%{skills}%"))

    q = q.order_by(Job.posted_at.desc(), Job.id.desc())
    total, total_pages, jobs = _paginate_query(q, page, limit)

    job_outs = []
    student_profile = None
    if user and user.role == "student":
        student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()

    for j in jobs:
        out = JobOut.model_validate(j)
        if student_profile:
            score, reasons = compute_job_match(student_profile, j)
            out.match_score = score
            out.match_reasons = reasons
        job_outs.append(out)

    response_data = {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "jobs": [j.model_dump() for j in job_outs],
    }

    cache_service.set(cache_key, response_data, ttl_seconds=180)
    return response_data


@router.get("/search", response_model=PaginatedJobsOut)
def search_jobs(
    q: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    posted_date: Optional[str] = Query(None),  # 24h, 7d, 30d
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Job).filter(Job.is_active == True)

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.company.ilike(term),
                Job.description.ilike(term),
                Job.location.ilike(term),
            )
        )

    if company:
        query = query.filter(func.lower(Job.company) == company.lower())
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if role:
        query = query.filter(Job.title.ilike(f"%{role}%"))
    if skills:
        query = query.filter(Job.description.ilike(f"%{skills}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if remote is not None:
        query = query.filter(Job.is_remote == remote)

    if posted_date:
        now = datetime.now(timezone.utc)
        if posted_date == "24h":
            query = query.filter(Job.posted_at >= now - timedelta(days=1))
        elif posted_date == "7d":
            query = query.filter(Job.posted_at >= now - timedelta(days=7))
        elif posted_date == "30d":
            query = query.filter(Job.posted_at >= now - timedelta(days=30))

    query = query.order_by(Job.posted_at.desc())
    total, total_pages, jobs = _paginate_query(query, page, limit)

    student_profile = None
    if user and user.role == "student":
        student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()

    job_outs = []
    for j in jobs:
        out = JobOut.model_validate(j)
        if student_profile:
            score, reasons = compute_job_match(student_profile, j)
            out.match_score = score
            out.match_reasons = reasons
        job_outs.append(out)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "jobs": job_outs,
    }


@router.get("/recommended", response_model=PaginatedJobsOut)
def recommended_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your student profile to view tailored recommendations.")

    all_jobs = db.query(Job).filter(Job.is_active == True).all()
    scored_jobs = []

    for j in all_jobs:
        out = JobOut.model_validate(j)
        score, reasons = compute_job_match(profile, j)
        out.match_score = score
        out.match_reasons = reasons
        scored_jobs.append(out)

    scored_jobs.sort(key=lambda x: x.match_score or 0.0, reverse=True)

    total = len(scored_jobs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    paginated_list = scored_jobs[offset : offset + limit]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "jobs": paginated_list,
    }


@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    cached = cache_service.get("companies:list")
    if cached:
        return cached

    results = (
        db.query(Job.company, func.count(Job.id).label("job_count"))
        .filter(Job.is_active == True)
        .group_by(Job.company)
        .order_by(Job.company.asc())
        .all()
    )

    companies = [{"company": r[0], "active_jobs": r[1]} for r in results]
    cache_service.set("companies:list", companies, ttl_seconds=600)
    return companies


@router.post("/sync")
def sync_external_jobs(
    background_tasks: BackgroundTasks,
    user: User = Depends(require_role("placement_officer")),
):
    background_tasks.add_task(run_job_sync_pipeline)
    return {"message": "Background job sync pipeline triggered successfully."}


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    out = JobOut.model_validate(job)
    if user and user.role == "student":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if profile:
            score, reasons = compute_job_match(profile, job)
            out.match_score = score
            out.match_reasons = reasons

    return out


@router.post("", response_model=JobOut, status_code=201)
def create_job(
    payload: JobCreate,
    user: User = Depends(require_role("placement_officer")),
    db: Session = Depends(get_db),
):
    job_data = payload.model_dump()
    if not job_data.get("posted_at"):
        job_data["posted_at"] = datetime.now(timezone.utc)
    if not job_data.get("last_checked_at"):
        job_data["last_checked_at"] = datetime.now(timezone.utc)

    job = Job(**job_data, posted_by=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    cache_service.delete_pattern("jobs:*")
    return job


@router.put("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    payload: JobUpdate,
    user: User = Depends(require_role("placement_officer")),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    cache_service.delete_pattern("jobs:*")
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    user: User = Depends(require_role("placement_officer")),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    cache_service.delete_pattern("jobs:*")
    return {"message": "Job deleted"}
