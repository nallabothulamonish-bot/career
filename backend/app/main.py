from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine

# Import all models so they register with Base.metadata before create_all()
from app.models import user, student_profile, job, application, resume_analysis, mock_interview, assessment  # noqa: F401

from app.routers import auth, students, jobs, applications, resume, interview, chatbot, assessments


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="CareerPilot AI API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(students.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(resume.router)
app.include_router(interview.router)
app.include_router(chatbot.router)
app.include_router(assessments.router)

