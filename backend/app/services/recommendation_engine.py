import re
from typing import Tuple, List, Dict, Any
from app.models.job import Job
from app.models.student_profile import StudentProfile
from app.services.nlp_utils import detect_skills

SENIOR_TITLE_KEYWORDS = [
    "director", "head", "manager", "senior", "staff", "principal",
    "lead", "architect", "vp", "vice president", "chief", "executive"
]

ENTRY_TITLE_KEYWORDS = [
    "intern", "internship", "graduate", "new grad", "associate",
    "junior", "trainee", "entry level", "fresher", "engineer i", "developer i"
]

TECH_ROLE_KEYWORDS = [
    "software", "developer", "engineer", "backend", "frontend", "full stack",
    "fullstack", "data", "ai", "machine learning", "cloud", "devops",
    "cybersecurity", "security", "qa", "quality assurance", "web", "mobile",
    "systems", "algorithm", "python", "java", "react", "c++"
]

NON_TECH_SALES_KEYWORDS = [
    "sales", "account executive", "business development", "marketing",
    "recruiter", "talent acquisition", "legal", "compliance", "finance associate"
]


def compute_job_match_detailed(student: StudentProfile, job: Job) -> Dict[str, Any]:
    match_reasons: List[str] = []
    mismatch_reasons: List[str] = []
    penalties = 0.0

    job_title_lower = (job.title or "").lower()
    job_desc_lower = (job.description or "").lower()
    job_req_lower = (job.requirements or "").lower()
    full_job_text = f"{job_title_lower} {job_desc_lower} {job_req_lower}"

    # 1. Skills Match (Weight: 40% -> Max 40 pts)
    student_skills = set([s.lower() for s in (student.skills or [])])
    if student.resume_text:
        student_skills.update(detect_skills(str(student.resume_text or "")))

    job_skills = set([s.lower() for s in (job.skills or job.required_skills or [])])
    if not job_skills and full_job_text.strip():
        job_skills = set(detect_skills(full_job_text))

    matched_skills = sorted(list(student_skills & job_skills))

    if job_skills:
        ratio = len(matched_skills) / max(1, len(job_skills))
        skill_score = min(40.0, ratio * 40.0)
        if matched_skills:
            match_reasons.append(f"Matched {len(matched_skills)} required skill(s): {', '.join(matched_skills[:4])}")
        else:
            mismatch_reasons.append("Low skill overlap with job requirements")
    else:
        skill_score = 25.0
        match_reasons.append("Open technology stack")

    # 2. Role / Title Relevance (Weight: 25% -> Max 25 pts)
    branch = (student.branch or "").lower()
    is_cs_it = any(b in branch for b in ["computer", "cs", "it", "software", "information technology"]) or not branch

    role_score = 0.0
    if is_cs_it:
        if any(re.search(rf"\b{re.escape(kw)}\b", job_title_lower) for kw in NON_TECH_SALES_KEYWORDS):
            role_score = 0.0
            penalties += 20.0
            mismatch_reasons.append("Sales / Business Development role — unrelated to Computer Science")
        elif any(re.search(rf"\b{re.escape(kw)}\b", job_title_lower) for kw in TECH_ROLE_KEYWORDS):
            role_score = 25.0
            match_reasons.append("Direct Computer Science / Tech role relevance")
        elif any(kw in full_job_text for kw in TECH_ROLE_KEYWORDS):
            role_score = 15.0
            match_reasons.append("Technical software component detected")
        else:
            role_score = 5.0
            mismatch_reasons.append("General non-technical job description")
    else:
        role_score = 15.0

    # 3. Experience & Seniority Fit (Weight: 20% -> Max 20 pts)
    matched_senior_terms = [kw for kw in SENIOR_TITLE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", job_title_lower)]
    matched_entry_terms = [kw for kw in ENTRY_TITLE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", job_title_lower) or (job.job_type and "intern" in job.job_type.lower())]

    seniority_score = 0.0
    if matched_senior_terms:
        seniority_score = 0.0
        penalties += 30.0
        mismatch_reasons.append(f"Senior leadership role ({', '.join(matched_senior_terms).title()}) — unsuited for students/freshers")
    elif matched_entry_terms:
        seniority_score = 20.0
        match_reasons.append(f"Entry-level / Internship suitable ({', '.join(matched_entry_terms).title()})")
    else:
        # Standard role (e.g. Software Engineer)
        seniority_score = 14.0
        match_reasons.append("Standard engineering role fit")

    # Check required experience years in text (e.g., 5+ years)
    exp_match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", full_job_text)
    if exp_match:
        years = int(exp_match.group(1))
        if years >= 4:
            penalties += 25.0
            mismatch_reasons.append(f"Requires {years}+ years industry experience")

    # 4. Location Preference (Weight: 10% -> Max 10 pts)
    pref_loc = getattr(student, "location_preference", None)
    job_loc_lower = (job.location or "").lower()

    location_score = 4.0
    if job.is_remote or "remote" in job_loc_lower:
        location_score = 10.0
        match_reasons.append("Remote work option available")
    elif pref_loc and pref_loc.lower() in job_loc_lower:
        location_score = 10.0
        match_reasons.append(f"Location matches your preference ({job.location})")
    elif any(hub in job_loc_lower for hub in ["bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "gurugram", "noida", "chennai", "india"]):
        location_score = 8.0
        match_reasons.append(f"Located in major tech hub ({job.location})")
    elif pref_loc:
        location_score = 2.0
        mismatch_reasons.append(f"Location ({job.location}) differs from preference")

    # 5. Job Type Preference (Weight: 5% -> Max 5 pts)
    job_type_score = 5.0
    if job.job_type in ["Full-Time", "Internship"]:
        match_reasons.append(f"Job type ({job.job_type}) aligns with placement goals")

    # Raw score calculation
    raw_score = skill_score + role_score + seniority_score + location_score + job_type_score - penalties
    clamped_score = max(5.0, min(98.0, raw_score))

    # Cap score if mismatch reasons exist
    if mismatch_reasons and clamped_score > 75.0:
        clamped_score = 75.0

    if not matched_skills and not matched_entry_terms and clamped_score > 80.0:
        clamped_score = 80.0

    return {
        "score": round(clamped_score, 1),
        "match_reasons": match_reasons[:4],
        "mismatch_reasons": mismatch_reasons[:4],
        "factor_scores": {
            "skills": round(skill_score, 1),
            "role_relevance": round(role_score, 1),
            "seniority_fit": round(seniority_score, 1),
            "location": round(location_score, 1),
            "job_type": round(job_type_score, 1),
            "penalties": round(penalties, 1),
        }
    }


def compute_job_match(student: StudentProfile, job: Job) -> Tuple[float, List[str]]:
    res = compute_job_match_detailed(student, job)
    return res["score"], res["match_reasons"]
