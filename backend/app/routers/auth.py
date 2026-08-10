from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, RoleEnum
from app.models.student_profile import StudentProfile
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=RoleEnum(payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.role == RoleEnum.student:
        db.add(StudentProfile(user_id=user.id))
        db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(token=token, user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role.value))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(token=token, user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role.value))


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, name=user.name, email=user.email, role=user.role.value)
