from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.schemas.student import StudentProfileUpdate, StudentProfileOut
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/me", response_model=StudentProfileOut)
def get_my_profile(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/me", response_model=StudentProfileOut)
def update_my_profile(
    payload: StudentProfileUpdate,
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)

    data = payload.model_dump(exclude_unset=True)
    if "education" in data and data["education"] is not None:
        data["education"] = [e for e in data["education"]]
    for key, value in data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("", response_model=list[StudentProfileOut])
def list_students(
    branch: str | None = Query(None),
    placed: bool | None = Query(None),
    user: User = Depends(require_role("placement_officer")),
    db: Session = Depends(get_db),
):
    q = db.query(StudentProfile)
    if branch:
        q = q.filter(StudentProfile.branch == branch)
    if placed is not None:
        q = q.filter(StudentProfile.placed == placed)
    return q.all()
