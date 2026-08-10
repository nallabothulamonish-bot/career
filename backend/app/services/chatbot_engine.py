"""
Hybrid Data-Aware AI Chatbot Engine for CareerPilot AI.

1. Queries live database first for jobs, applications, eligibility, and stats.
2. Calls Anthropic LLM (if configured) for general career questions.
3. Provides context-aware deterministic fallbacks when no LLM API key exists.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.job import Job
from app.models.application import Application
from app.models.student_profile import StudentProfile
from app.services import llm_service
from app.services.recommendation_engine import compute_job_match

logger = logging.getLogger("careerpilot.chatbot")


def _get_active_jobs_summary(db: Session, limit: int = 5) -> str:
    jobs = (
        db.query(Job)
        .filter(Job.is_active == True)
        .order_by(Job.posted_at.desc())
        .limit(limit)
        .all()
    )
    total_count = db.query(Job).filter(Job.is_active == True).count()
    if not jobs:
        return "We currently have no active job postings. Check back soon as our sync service runs periodically!"

    lines = [f"• **{j.title}** at {j.company} ({j.location} · {j.job_type})" for j in jobs]
    return (
        f"We currently have **{total_count} active job opportunities** synced on CareerPilot:\n"
        + "\n".join(lines)
        + "\n\nHead to the **Drives & Jobs** tab to search, filter, and apply directly!"
    )


def _get_user_application_status(db: Session, user_id: int | None) -> str:
    if not user_id:
        return "Please log in to your student account to check your application status."

    apps = db.query(Application).filter(Application.student_id == user_id).all()
    if not apps:
        return "You haven't submitted any job applications yet. Browse the **Drives & Jobs** tab to explore opportunities and apply!"

    lines = []
    for a in apps:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        job_title = job.title if job else f"Job #{a.job_id}"
        company = job.company if job else "Company"
        lines.append(f"• **{job_title}** at {company}: Status **{a.status.value}** (Match score: {a.match_score}%)")

    return f"Here is the status of your **{len(apps)} application(s)**:\n" + "\n".join(lines)


def _get_student_eligibility_report(db: Session, user_id: int | None) -> str:
    if not user_id:
        return "Please log in so I can analyze your student profile against active job openings."

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        return "Please complete your Student Profile (CGPA, Branch, Skills) first so I can compute eligibility and match scores."

    active_jobs = db.query(Job).filter(Job.is_active == True).all()
    if not active_jobs:
        return "There are no active jobs in the database right now."

    eligible_jobs = []
    for j in active_jobs:
        score, reasons = compute_job_match(profile, j)
        if score >= 60.0:
            eligible_jobs.append((j, score, reasons))

    eligible_jobs.sort(key=lambda x: x[1], reverse=True)

    if not eligible_jobs:
        return f"Based on your profile ({profile.branch}, CGPA: {profile.cgpa}), try adding more skills to your profile or resume to boost your match scores."

    lines = [f"• **{j.title}** at {j.company}: **{score}% match** ({reasons[0] if reasons else 'Qualified'})" for j, score, reasons in eligible_jobs[:5]]
    return (
        f"Great news! Based on your profile (**{profile.branch}**, CGPA **{profile.cgpa}**), you match **{len(eligible_jobs)} active role(s)**:\n"
        + "\n".join(lines)
    )


def _get_company_list(db: Session) -> str:
    companies = (
        db.query(Job.company, func.count(Job.id))
        .filter(Job.is_active == True)
        .group_by(Job.company)
        .order_by(Job.company.asc())
        .limit(10)
        .all()
    )
    if not companies:
        return "No companies currently listed in the database."

    lines = [f"• **{c[0]}** ({c[1]} active role(s))" for c in companies]
    return "Here are top hiring companies currently active on CareerPilot:\n" + "\n".join(lines)


DATA_INTENTS = [
    {
        "name": "open_jobs",
        "keywords": ["open job", "active job", "job opening", "vacancies", "available jobs", "drives", "hiring", "openings"],
        "handler": lambda db, uid: _get_active_jobs_summary(db),
    },
    {
        "name": "my_applications",
        "keywords": ["my application", "application status", "applied", "status of my application", "my status"],
        "handler": lambda db, uid: _get_user_application_status(db, uid),
    },
    {
        "name": "eligibility",
        "keywords": ["eligible", "eligibility", "am i eligible", "my match", "recommended jobs", "fit for me"],
        "handler": lambda db, uid: _get_student_eligibility_report(db, uid),
    },
    {
        "name": "companies",
        "keywords": ["companies", "who is hiring", "company list", "employers", "recruiting"],
        "handler": lambda db, uid: _get_company_list(db),
    },
]


def _match_intent(message: str) -> str | None:
    msg_lower = message.lower()
    for intent in DATA_INTENTS:
        for kw in intent["keywords"]:
            if kw in msg_lower:
                return intent["name"]
    return None


def get_chatbot_reply(message: str, db: Session, user_id: int | None = None) -> str:
    if not message or not message.strip():
        return "Hello! I'm your CareerPilot AI Assistant. Ask me about active jobs, your applications, eligibility, resume feedback, or interview prep!"

    msg_clean = message.strip()

    # 1. Query Database First for Data-Specific Questions
    matched_intent_name = _match_intent(msg_clean)
    if matched_intent_name:
        for intent in DATA_INTENTS:
            if intent["name"] == matched_intent_name:
                return intent["handler"](db, user_id)

    # 2. Call Anthropic LLM Service if API key is configured
    if llm_service.is_available():
        try:
            prompt = (
                f"You are CareerPilot AI, an expert career advisor and placement consultant. "
                f"Answer the candidate's question helpfully, concisely, and professionally.\n"
                f"Question: {msg_clean}"
            )
            # Use general feedback / completion wrapper if supported
            reply = llm_service.generate_answer_feedback("Career Advice", msg_clean, "general")
            if reply and isinstance(reply, dict) and "feedback" in reply:
                return "\n".join(reply["feedback"])
        except Exception as e:
            logger.error(f"LLM chatbot generation error: {e}")

    # 3. Context-Aware Deterministic Fallback Templates
    lower = msg_clean.lower()
    if "resume" in lower or "cv" in lower:
        return (
            "To optimize your resume for ATS screening:\n"
            "1. Use standard section titles (Experience, Education, Skills).\n"
            "2. Quantify achievements with metrics (e.g. 'Increased speed by 35%').\n"
            "3. Upload your PDF in the **Resume Analyzer** tab to receive an instant ATS score and keyword gap analysis!"
        )
    if "interview" in lower or "prepare" in lower or "mock" in lower:
        return (
            "To excel in technical & behavioral interviews:\n"
            "1. Use the STAR method (Situation, Task, Action, Result) for behavioral questions.\n"
            "2. Focus on clear ownership language ('I built', 'I analyzed').\n"
            "3. Practice in the **AI Mock Interview** section to get real-time voice evaluation and feedback!"
        )
    if "salary" in lower or "ctc" in lower or "stipend" in lower or "pay" in lower:
        return (
            "Compensation packages vary by role and company. Active postings on CareerPilot include competitive market CTC for full-time graduate engineers and monthly stipends for internship positions."
        )
    if "contact" in lower or "help" in lower or "support" in lower:
        return (
            "You can manage your profile in the **Profile** tab, analyze documents in **Resume Analyzer**, or check active opportunities in **Drives & Jobs**."
        )

    return (
        f"I understand you're asking about '{msg_clean}'. You can explore active job drives, check your application status, analyze your resume, or practice voice mock interviews directly on the platform!"
    )
