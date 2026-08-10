from typing import Tuple, List
from app.models.job import Job
from app.models.student_profile import StudentProfile
from app.services.nlp_utils import detect_skills, tokenize


def compute_job_match(student: StudentProfile, job: Job) -> Tuple[float, List[str]]:
    reasons = []

    # 1. Skill Coverage (Max 50 pts)
    job_skills = set([s.lower() for s in (job.skills or job.required_skills or [])])
    student_skills = set([s.lower() for s in (student.skills or [])])

    if not job_skills and job.description:
        job_skills = set(detect_skills(job.title + " " + job.description))

    matched_skills = sorted(list(student_skills & job_skills))

    if job_skills:
        skill_ratio = len(matched_skills) / len(job_skills)
        skill_score = min(50.0, skill_ratio * 50.0)
    else:
        skill_score = 35.0  # Open skill baseline

    if matched_skills:
        reasons.append(f"Matches {len(matched_skills)} required skill(s): {', '.join(matched_skills[:4])}")
    elif not job_skills:
        reasons.append("Open tech stack — suitable for all general programming backgrounds")

    # 2. Branch Alignment (Max 20 pts)
    branch = (student.branch or "").lower()
    eligible_branches = [b.lower() for b in (job.eligible_branches or [])]
    job_text = (job.title + " " + job.description).lower()

    if not eligible_branches or any(b in branch or branch in b for b in eligible_branches):
        branch_score = 20.0
        if student.branch:
            reasons.append(f"Eligible for {student.branch} candidates")
    elif "computer" in branch or "it" in branch or "software" in branch:
        if any(term in job_text for term in ["software", "developer", "engineer", "data", "web", "frontend", "backend"]):
            branch_score = 18.0
            reasons.append("Strong fit for CS/IT specialization")
        else:
            branch_score = 10.0
    else:
        branch_score = 12.0

    # 3. Location & Remote Preference (Max 15 pts)
    if job.is_remote:
        location_score = 15.0
        reasons.append("Remote work option available")
    elif student.location_preference and student.location_preference.lower() in job.location.lower():
        location_score = 15.0
        reasons.append(f"Location matches your preference ({job.location})")
    elif "on-campus" in job.location.lower() or "hybrid" in job.location.lower():
        location_score = 12.0
    else:
        location_score = 10.0

    # 4. Job Type Alignment (Max 15 pts)
    job_type_score = 15.0
    if job.job_type == "Full-Time":
        reasons.append("Full-Time role matching graduate placement goals")

    total_score = min(100.0, max(40.0, skill_score + branch_score + location_score + job_type_score))
    return round(total_score, 1), reasons[:4]
