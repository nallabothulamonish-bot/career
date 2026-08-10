"""
Intent-based career assistant chatbot. Matches user message against known
intents via keyword scoring, then pulls live data from MySQL to personalize
the reply. No external API required.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.job import Job, JobStatus
from app.models.application import Application
from app.models.student_profile import StudentProfile


def _open_drives_reply(db: Session) -> str:
    jobs = (
        db.query(Job)
        .filter(Job.status == JobStatus.open, Job.application_deadline >= datetime.utcnow())
        .order_by(Job.application_deadline.asc())
        .limit(5)
        .all()
    )
    if not jobs:
        return "There are no open drives right now. Check back soon!"
    lines = [f"• {j.title} at {j.company} (deadline: {j.application_deadline.strftime('%d %b %Y')})" for j in jobs]
    return "Here are the current open drives:\n" + "\n".join(lines)


def _application_status_reply(db: Session, user_id: int | None) -> str:
    if not user_id:
        return "Please log in to check your application status."
    apps = db.query(Application).filter(Application.student_id == user_id).all()
    if not apps:
        return "You haven't applied to any drives yet."
    lines = []
    for a in apps:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        if job:
            lines.append(f"• {job.title} at {job.company}: {a.status.value} (match {a.match_score}%)")
    return "Your applications:\n" + "\n".join(lines)


def _eligibility_reply(db: Session, user_id: int | None) -> str:
    if not user_id:
        return "Log in and I can check eligibility against your profile."
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        return "Please complete your profile first so I can check eligibility for you."
    jobs = db.query(Job).filter(Job.status == JobStatus.open).all()
    eligible = [
        j for j in jobs
        if profile.cgpa >= j.min_cgpa and (not j.eligible_branches or profile.branch in j.eligible_branches)
    ]
    if not eligible:
        return "Based on your profile, you're not currently eligible for any open drive."
    return "You're eligible for: " + ", ".join(f"{j.title} ({j.company})" for j in eligible)


INTENTS = [
    {"name": "greeting", "keywords": ["hi", "hello", "hey", "good morning", "good evening"],
     "reply": lambda db, uid: "Hi! I'm your placement assistant. Ask about open drives, eligibility, application status, resume tips, or mock interviews."},
    {"name": "open_drives", "keywords": ["open drive", "current drive", "jobs available", "openings", "vacancies", "new jobs"],
     "reply": lambda db, uid: _open_drives_reply(db)},
    {"name": "application_status", "keywords": ["my application", "application status", "shortlisted", "my status"],
     "reply": lambda db, uid: _application_status_reply(db, uid)},
    {"name": "eligibility", "keywords": ["eligible", "eligibility", "criteria", "cgpa required", "am i eligible"],
     "reply": lambda db, uid: _eligibility_reply(db, uid)},
    {"name": "resume_tips", "keywords": ["resume tip", "improve resume", "resume help", "cv tip"],
     "reply": lambda db, uid: "Try our Resume Analyzer for a free ATS score! Quick tips: use bullet points, quantify achievements with numbers, and mirror keywords from the job description."},
    {"name": "mock_interview", "keywords": ["mock interview", "interview practice", "practice interview"],
     "reply": lambda db, uid: "Head to the Mock Interview section — pick a role, answer a few questions, and get instant AI feedback with a score."},
    {"name": "match_score", "keywords": ["match score", "how well do i match"],
     "reply": lambda db, uid: "Match score = 60% required-skill coverage + 40% TF-IDF text similarity between your resume and the job description."},
    {"name": "thanks", "keywords": ["thank", "thanks"],
     "reply": lambda db, uid: "You're welcome! Good luck with your placements 🎓"},
]


def _score_intent(message: str, keywords: list[str]) -> int:
    lower = message.lower()
    return sum(len(kw) for kw in keywords if kw in lower)


def get_chatbot_reply(message: str, db: Session, user_id: int | None = None) -> str:
    if not message or not message.strip():
        return "Ask me about open drives, your application status, eligibility, resume tips, or mock interviews."

    best_intent, best_score = None, 0
    for intent in INTENTS:
        s = _score_intent(message, intent["keywords"])
        if s > best_score:
            best_score, best_intent = s, intent

    if not best_intent:
        return "I'm not sure about that yet. Try asking about 'open drives', 'my application status', 'eligibility', 'resume tips', or 'mock interview'."

    return best_intent["reply"](db, user_id)
