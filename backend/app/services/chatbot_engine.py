"""
Database-First AI Career Assistant Engine for CareerPilot AI.

Supports 9+ Core Intents:
- JOB_SEARCH
- COMPANY_SEARCH
- LOCATION_SEARCH
- INTERNSHIP_SEARCH
- RECOMMENDATIONS
- APPLICATION_STATUS
- RESUME_HELP
- INTERVIEW_HELP
- GENERAL_CAREER
- MULTIPLE_REQUESTS

Queries live database first for all job/company/location/internship/recommendation/application questions.
Never invents fake job openings.
Integrates optional Anthropic LLM formatting for general career guidance.
"""
import uuid
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.job import Job
from app.models.application import Application
from app.models.student_profile import StudentProfile
from app.services import llm_service
from app.services.recommendation_engine import compute_job_match
from app.schemas.chatbot import JobSummaryOut, ChatResponse

logger = logging.getLogger("careerpilot.chatbot")

SESSION_STORE: Dict[str, Dict[str, Any]] = {}

LOCATION_SYNONYMS = {
    "bangalore": ["bangalore", "bengaluru"],
    "bengaluru": ["bangalore", "bengaluru"],
    "hyderabad": ["hyderabad"],
    "chennai": ["chennai"],
    "pune": ["pune"],
    "mumbai": ["mumbai"],
    "gurugram": ["gurugram", "gurgaon"],
    "gurgaon": ["gurugram", "gurgaon"],
    "noida": ["noida"],
    "delhi": ["delhi", "ncr"],
    "remote": ["remote"],
    "india": ["india"],
}

KNOWN_SKILLS = [
    "python", "javascript", "react", "node", "java", "c++", "c#", "c", "sql",
    "golang", "aws", "docker", "kubernetes", "linux", "git", "machine learning",
    "data science", "data engineer", "devops", "cloud", "security", "cyber security",
    "qa", "ai", "artificial intelligence"
]


def _get_or_create_session(session_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    if not session_id or session_id not in SESSION_STORE:
        new_id = session_id if session_id else str(uuid.uuid4())
        SESSION_STORE[new_id] = {
            "location": None,
            "company": None,
            "job_type": None,
            "skill": None,
            "last_intent": None,
        }
        return new_id, SESSION_STORE[new_id]
    return session_id, SESSION_STORE[session_id]


COMPANY_STOPWORDS = {
    "me", "the", "all", "active", "some", "open", "software", "developer",
    "engineer", "internship", "intern", "data", "cloud", "full time",
    "part time", "qa", "devops", "ai", "machine learning", "tech", "role",
    "roles", "jobs", "job", "opening", "openings", "drive", "drives", "position", "positions"
}


def _extract_company_from_message(msg: str, db: Session) -> Optional[str]:
    msg_lower = msg.lower().strip()

    # 1. Match against distinct active companies in DB first
    try:
        distinct_companies = [r[0] for r in db.query(Job.company).filter(Job.is_active == True).distinct().all() if r[0]]
        for comp in distinct_companies:
            comp_lower = comp.lower()
            if comp_lower in msg_lower and len(comp_lower) >= 3:
                return comp
    except Exception as e:
        logger.error(f"Error querying company list: {e}")

    # 2. Regex patterns for company extraction with stopword guard
    patterns = [
        r"(?:jobs|openings|roles|drives|vacancies)\s+(?:at|for|with)\s+([a-zA-Z0-9\.\-\s]+)",
        r"(?:show|list|get|find)\s+([a-zA-Z0-9\.\-\s]+)\s+(?:jobs|openings|roles|drives)",
        r"any\s+openings\s+at\s+([a-zA-Z0-9\.\-\s]+)",
    ]
    for pat in patterns:
        m = re.search(pat, msg_lower)
        if m:
            candidate = m.group(1).strip()
            tokens = [t for t in candidate.split() if t.lower() not in COMPANY_STOPWORDS]
            if tokens:
                clean_candidate = " ".join(tokens)
                if len(clean_candidate) >= 3:
                    return clean_candidate.capitalize()

    return None


def _extract_location_from_message(msg_lower: str) -> Optional[str]:
    for loc in LOCATION_SYNONYMS:
        if re.search(rf"\b{loc}\b", msg_lower):
            return loc
    return None


def _extract_skill_from_message(msg_lower: str) -> Optional[str]:
    for sk in KNOWN_SKILLS:
        if re.search(rf"\b{re.escape(sk)}\b", msg_lower):
            return sk
    return None


def _detect_intent_and_entities(msg: str, db: Session) -> Tuple[str, Dict[str, Any]]:
    msg_lower = msg.lower().strip()

    # 1. Multi-intent / Multiple Question check
    question_count = msg_lower.count("?")
    has_and = " and " in msg_lower or " also " in msg_lower
    if question_count > 1 or (has_and and len(msg_lower.split()) > 10):
        topics = 0
        if any(k in msg_lower for k in ["application", "applied", "status"]): topics += 1
        if any(k in msg_lower for k in ["resume", "cv"]): topics += 1
        if any(k in msg_lower for k in ["interview", "mock"]): topics += 1
        if any(k in msg_lower for k in ["job", "opening", "internship", "stripe", "bangalore"]): topics += 1
        if topics >= 2:
            return "MULTIPLE_REQUESTS", {}

    # 2. Application Status
    if any(k in msg_lower for k in ["application status", "my application", "my status", "status of my application", "show my applications", "applications applied"]):
        return "APPLICATION_STATUS", {}

    # 3. Recommendations / Skill Matching
    if any(k in msg_lower for k in ["match my skills", "match for my profile", "recommended jobs", "best jobs for my profile", "recommend jobs", "recommendations", "am i eligible", "my match"]):
        return "RECOMMENDATIONS", {}

    # 4. Resume Help
    if any(k in msg_lower for k in ["resume tips", "improve my resume", "resume feedback", "ats score", "cv guidance", "resume help"]):
        return "RESUME_HELP", {}

    # 5. Interview Help
    if any(k in msg_lower for k in ["prepare for", "interview questions", "interview help", "mock interview", "technical interview", "behavioral interview", "star method"]):
        return "INTERVIEW_HELP", {}

    # 6. Company Search
    extracted_company = _extract_company_from_message(msg, db)
    if extracted_company:
        return "COMPANY_SEARCH", {"company": extracted_company}

    # 7. Internship Search
    if any(k in msg_lower for k in ["internship", "internships", "intern", "co-op", "stipend"]):
        loc = _extract_location_from_message(msg_lower)
        sk = _extract_skill_from_message(msg_lower)
        return "INTERNSHIP_SEARCH", {"location": loc, "skill": sk, "job_type": "Internship"}

    # 8. Location Search / Job Search
    loc = _extract_location_from_message(msg_lower)
    sk = _extract_skill_from_message(msg_lower)
    has_job_kw = any(k in msg_lower for k in ["job", "jobs", "opening", "openings", "drive", "drives", "role", "roles", "developer", "engineer", "hiring", "fresher", "graduate", "vacancy", "vacancies"])

    if loc and (has_job_kw or sk):
        return "LOCATION_SEARCH", {"location": loc, "skill": sk}

    if has_job_kw or sk:
        return "JOB_SEARCH", {"location": loc, "skill": sk}

    return "GENERAL_CAREER", {}


def get_chatbot_reply(
    message: str,
    db: Session,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> ChatResponse:
    sid, session_ctx = _get_or_create_session(session_id)

    if not message or not message.strip():
        return ChatResponse(
            message="Hello! I'm your CareerPilot AI Assistant. Ask me about active jobs, company drives, eligibility, resume tips, or interview prep!",
            intent="GENERAL_CAREER",
            jobs=[],
            suggestions=["Show Stripe jobs", "What jobs match my skills?", "Show me internships in Hyderabad", "Give me resume tips"],
            session_id=sid,
        )

    clean_msg = message.strip()
    msg_lower = clean_msg.lower()

    # Detect Intent & Extract Entities
    intent, entities = _detect_intent_and_entities(clean_msg, db)

    # Update Session Context
    if entities.get("location"):
        session_ctx["location"] = entities["location"]
    if entities.get("company"):
        session_ctx["company"] = entities["company"]
    if entities.get("job_type"):
        session_ctx["job_type"] = entities["job_type"]
    if entities.get("skill"):
        session_ctx["skill"] = entities["skill"]
    session_ctx["last_intent"] = intent

    # Fetch student profile if logged in
    student_profile = None
    if user_id:
        student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    jobs_out: List[JobSummaryOut] = []
    response_text = ""
    suggestions: List[str] = []

    try:
        # MULTIPLE REQUESTS
        if intent == "MULTIPLE_REQUESTS":
            response_text = "I noticed your message contains multiple questions! Please send one request at a time or click a suggestion below so I can give you the most precise response."
            suggestions = ["Show Stripe jobs", "What jobs match my skills?", "What is my application status?", "Give me resume tips"]

        # 1. COMPANY SEARCH
        elif intent == "COMPANY_SEARCH":
            company_name = entities.get("company") or session_ctx.get("company")
            query = db.query(Job).filter(Job.is_active == True)
            if company_name:
                query = query.filter(Job.company.ilike(f"%{company_name}%"))

            matched_jobs = query.order_by(Job.posted_at.desc()).limit(5).all()

            if not matched_jobs:
                response_text = f"No active positions currently found for **{company_name}**. Explore other top hiring drives on CareerPilot!"
            else:
                response_text = f"Found **{len(matched_jobs)} active role(s)** at **{company_name}**:"
                for j in matched_jobs:
                    score = None
                    if student_profile:
                        s_val, _ = compute_job_match(student_profile, j)
                        score = round(s_val, 1)

                    jobs_out.append(JobSummaryOut(
                        id=j.id,
                        company=j.company,
                        title=j.title,
                        location=j.location,
                        job_type=j.job_type,
                        match_score=score,
                        application_url=j.application_url,
                        source=j.source,
                    ))
            suggestions = ["Show internships only", "What jobs match my skills?", "Check application status", "Give me resume tips"]

        # 2. LOCATION SEARCH & JOB SEARCH
        elif intent in ["LOCATION_SEARCH", "JOB_SEARCH"]:
            loc_key = entities.get("location") or session_ctx.get("location")
            skill_key = entities.get("skill") or session_ctx.get("skill")

            query = db.query(Job).filter(Job.is_active == True)

            if loc_key:
                synonyms = LOCATION_SYNONYMS.get(loc_key.lower(), [loc_key])
                loc_filters = [Job.location.ilike(f"%{s}%") for s in synonyms]
                query = query.filter(or_(*loc_filters))

            if skill_key:
                query = query.filter(or_(Job.title.ilike(f"%{skill_key}%"), Job.description.ilike(f"%{skill_key}%")))

            matched_jobs = query.order_by(Job.posted_at.desc()).limit(5).all()

            if not matched_jobs:
                loc_str = f" in **{loc_key.capitalize()}**" if loc_key else ""
                sk_str = f" for **{skill_key.capitalize()}**" if skill_key else ""
                response_text = f"No active roles found matching your query{loc_str}{sk_str}. Check out other open drives!"
            else:
                loc_str = f" in **{loc_key.capitalize()}**" if loc_key else ""
                sk_str = f" for **{skill_key.capitalize()}**" if skill_key else ""
                response_text = f"Found **{len(matched_jobs)} active job(s)**{loc_str}{sk_str}:"
                for j in matched_jobs:
                    score = None
                    if student_profile:
                        s_val, _ = compute_job_match(student_profile, j)
                        score = round(s_val, 1)

                    jobs_out.append(JobSummaryOut(
                        id=j.id,
                        company=j.company,
                        title=j.title,
                        location=j.location,
                        job_type=j.job_type,
                        match_score=score,
                        application_url=j.application_url,
                        source=j.source,
                    ))
            suggestions = ["Show internships only", "What jobs match my skills?", "Analyze my resume", "Start mock interview"]

        # 3. INTERNSHIP SEARCH
        elif intent == "INTERNSHIP_SEARCH":
            loc_key = entities.get("location") or session_ctx.get("location")
            skill_key = entities.get("skill") or session_ctx.get("skill")

            query = db.query(Job).filter(
                Job.is_active == True,
                or_(Job.job_type.ilike("%intern%"), Job.title.ilike("%intern%"))
            )

            if loc_key:
                synonyms = LOCATION_SYNONYMS.get(loc_key.lower(), [loc_key])
                query = query.filter(or_(*[Job.location.ilike(f"%{s}%") for s in synonyms]))

            if skill_key:
                query = query.filter(or_(Job.title.ilike(f"%{skill_key}%"), Job.description.ilike(f"%{skill_key}%")))

            matched_jobs = query.order_by(Job.posted_at.desc()).limit(5).all()

            if not matched_jobs:
                loc_str = f" in **{loc_key.capitalize()}**" if loc_key else ""
                response_text = f"No active internships currently found{loc_str}. Check back as our sync pipeline updates periodically!"
            else:
                loc_str = f" in **{loc_key.capitalize()}**" if loc_key else ""
                response_text = f"Found **{len(matched_jobs)} active internship(s)**{loc_str}:"
                for j in matched_jobs:
                    score = None
                    if student_profile:
                        s_val, _ = compute_job_match(student_profile, j)
                        score = round(s_val, 1)

                    jobs_out.append(JobSummaryOut(
                        id=j.id,
                        company=j.company,
                        title=j.title,
                        location=j.location,
                        job_type=j.job_type,
                        match_score=score,
                        application_url=j.application_url,
                        source=j.source,
                    ))
            suggestions = ["What jobs match my skills?", "Show Stripe jobs", "Analyze my resume", "Start mock interview"]

        # 4. RECOMMENDATIONS
        elif intent == "RECOMMENDATIONS":
            if not student_profile:
                # Return top active drives with match score baseline explanation
                top_jobs = db.query(Job).filter(Job.is_active == True).order_by(Job.posted_at.desc()).limit(5).all()
                response_text = "To receive personalized match percentages, complete your Student Profile! Here are top active opportunities on CareerPilot:"
                for j in top_jobs:
                    jobs_out.append(JobSummaryOut(
                        id=j.id,
                        company=j.company,
                        title=j.title,
                        location=j.location,
                        job_type=j.job_type,
                        match_score=None,
                        application_url=j.application_url,
                        source=j.source,
                    ))
            else:
                active_jobs = db.query(Job).filter(Job.is_active == True).all()
                scored_jobs = []
                for j in active_jobs:
                    score, _ = compute_job_match(student_profile, j)
                    scored_jobs.append((j, score))

                scored_jobs.sort(key=lambda x: x[1], reverse=True)
                top_matches = scored_jobs[:5]

                response_text = f"Based on your profile (**{student_profile.branch}**, CGPA **{student_profile.cgpa}**), here are your top recommended matches:"
                for j, score in top_matches:
                    jobs_out.append(JobSummaryOut(
                        id=j.id,
                        company=j.company,
                        title=j.title,
                        location=j.location,
                        job_type=j.job_type,
                        match_score=round(score, 1),
                        application_url=j.application_url,
                        source=j.source,
                    ))
            suggestions = ["Show internships only", "Check application status", "Analyze my resume", "Start mock interview"]

        # 5. APPLICATION STATUS
        elif intent == "APPLICATION_STATUS":
            if not user_id:
                response_text = "Please log in to your student account to check your submitted application status."
            else:
                apps = db.query(Application).filter(Application.student_id == user_id).all()
                if not apps:
                    response_text = "You haven't submitted any applications yet. Explore the **Drives & Jobs** tab or ask me for recommendations!"
                else:
                    lines = []
                    for a in apps[:5]:
                        j = db.query(Job).filter(Job.id == a.job_id).first()
                        title = j.title if j else f"Job #{a.job_id}"
                        company = j.company if j else "Company"
                        lines.append(f"• **{title}** at {company}: Status **{a.status.value}** (Match: {a.match_score:.0f}%)")
                    response_text = f"Here is the status of your **{len(apps)} application(s)**:\n" + "\n".join(lines)
            suggestions = ["What jobs match my skills?", "Show Stripe jobs", "Analyze my resume", "Start mock interview"]

        # 6. RESUME HELP
        elif intent == "RESUME_HELP":
            if llm_service.is_available():
                llm_reply = llm_service.generate_career_assistant_reply(clean_msg, "RESUME_HELP", "Standard ATS format advice")
                if llm_reply:
                    response_text = llm_reply
            if not response_text:
                response_text = (
                    "Here are essential resume optimization tips:\n"
                    "1. Use standard, scannable section headers (Education, Experience, Skills, Projects).\n"
                    "2. Include quantifiable achievements (e.g. 'Improved efficiency by 35%').\n"
                    "3. Head to the **Resume Analyzer** tab to upload your document for an instant ATS compliance score!"
                )
            suggestions = ["Analyze my resume", "What jobs match my skills?", "Start mock interview", "Show Stripe jobs"]

        # 7. INTERVIEW HELP
        elif intent == "INTERVIEW_HELP":
            if llm_service.is_available():
                llm_reply = llm_service.generate_career_assistant_reply(clean_msg, "INTERVIEW_HELP", "STAR interview technique guidance")
                if llm_reply:
                    response_text = llm_reply
            if not response_text:
                response_text = (
                    "To ace technical and behavioral interviews:\n"
                    "1. Use the STAR framework (Situation, Task, Action, Result) for structured answers.\n"
                    "2. Emphasize individual technical contributions ('I architected', 'I debugged').\n"
                    "3. Head to the **AI Mock Interview** tab to practice voice questions with real-time feedback!"
                )
            suggestions = ["Start mock interview", "What jobs match my skills?", "Give me resume tips", "Show Stripe jobs"]

        # 8. GENERAL CAREER / FALLBACK
        else:
            if llm_service.is_available():
                llm_reply = llm_service.generate_career_assistant_reply(clean_msg, "GENERAL_CAREER", "General career consultant context")
                if llm_reply:
                    response_text = llm_reply

            if not response_text:
                response_text = (
                    "I am your CareerPilot AI Assistant! You can ask me to search active job drives by company or location, check your eligibility, track application status, or get resume and interview preparation guidance."
                )
            suggestions = ["Show Stripe jobs", "What jobs match my skills?", "Show me internships in Hyderabad", "Give me resume tips"]

    except Exception as e:
        logger.error(f"Error processing chatbot request: {e}")
        response_text = "I encountered an issue querying the database. Please try asking again or explore the Drives tab directly!"
        suggestions = ["Show Stripe jobs", "What jobs match my skills?", "Give me resume tips"]

    return ChatResponse(
        message=response_text,
        intent=intent,
        jobs=jobs_out,
        suggestions=suggestions,
        session_id=sid,
    )
