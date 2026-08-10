"""
Resume Analyzer — ATS-style scoring engine.

Evaluates a plain-text resume across four dimensions:
  1. Structure     — presence of key sections (summary, experience, education, skills, projects)
  2. Readability    — sentence length, word count, bullet-point usage heuristics
  3. Keyword/Skill coverage — vs. a target job description (if provided) using the same
                      TF-IDF resume_matcher engine, else vs. the general SKILL_BANK
  4. Impact         — density of action verbs and quantified achievements (numbers/%)

Combines them into an overall ATS score (0-100) with human-readable, prioritized
suggestions — the kind a career coach would give.
"""
import re

from app.services.nlp_utils import (
    detect_skills, word_count, sentence_count, count_action_verbs,
)
from app.services.resume_matcher import match_resume_to_job

SECTION_PATTERNS = {
    "contact": r"(email|phone|linkedin|github)",
    "summary": r"(summary|objective|profile)",
    "experience": r"(experience|internship|work history|employment)",
    "education": r"(education|degree|university|college|b\.?tech|b\.?e\.?|m\.?tech)",
    "skills": r"(skills|technologies|tech stack|proficienc)",
    "projects": r"(projects?|portfolio)",
}


def _structure_score(text: str) -> tuple[float, list[str], list[str]]:
    lower = text.lower()
    present = [name for name, pat in SECTION_PATTERNS.items() if re.search(pat, lower)]
    missing = [name for name in SECTION_PATTERNS if name not in present]
    score = (len(present) / len(SECTION_PATTERNS)) * 100
    return round(score, 1), present, missing


def _readability_score(text: str) -> tuple[float, list[str]]:
    notes = []
    wc = word_count(text)
    sc = sentence_count(text) or 1
    avg_sentence_len = wc / sc

    score = 100.0
    if wc < 150:
        score -= 30
        notes.append("Your resume looks quite short — aim for 300–600 words for a solid 1-page resume.")
    elif wc > 900:
        score -= 20
        notes.append("Your resume is lengthy — trim it to 1 page (freshers) or 2 pages (experienced).")

    if avg_sentence_len > 30:
        score -= 15
        notes.append("Some lines are very long — break them into concise bullet points (1 line each).")

    bullet_count = len(re.findall(r"(^|\n)\s*[•\-\*]\s", text))
    if bullet_count < 3:
        score -= 15
        notes.append("Use bullet points to list achievements — they're easier for ATS and recruiters to scan.")

    return max(0.0, round(score, 1)), notes


def _impact_score(text: str) -> tuple[float, list[str], list[str]]:
    strengths, notes = [], []
    verbs_found = count_action_verbs(text)
    numbers_found = len(re.findall(r"\b\d+%?\b", text))

    score = 0.0
    if verbs_found >= 5:
        score += 50
        strengths.append(f"Good use of strong action verbs ({verbs_found} detected) — shows ownership and impact.")
    elif verbs_found >= 2:
        score += 30
        notes.append("Add more action verbs (e.g., 'led', 'built', 'optimized') to start your bullet points.")
    else:
        notes.append("Start bullet points with action verbs instead of passive phrases like 'responsible for'.")

    if numbers_found >= 3:
        score += 50
        strengths.append(f"Nice — {numbers_found} quantified results found (numbers/%), which recruiters love.")
    elif numbers_found >= 1:
        score += 25
        notes.append("Quantify more achievements with numbers (e.g., 'reduced load time by 40%').")
    else:
        notes.append("Add measurable outcomes — numbers, percentages, or scale — to demonstrate real impact.")

    return round(score, 1), strengths, notes


def analyze_resume(resume_text: str, target_job_title: str = "", target_job_description: str = "") -> dict:
    resume_text = resume_text or ""
    strengths: list[str] = []
    suggestions: list[str] = []

    structure_score, present_sections, missing_sections = _structure_score(resume_text)
    if missing_sections:
        suggestions.append(f"Add missing section(s): {', '.join(missing_sections)}.")
    if present_sections:
        strengths.append(f"Well-organized with clear section(s): {', '.join(present_sections)}.")

    readability, readability_notes = _readability_score(resume_text)
    suggestions.extend(readability_notes)

    impact_score, impact_strengths, impact_notes = _impact_score(resume_text)
    strengths.extend(impact_strengths)
    suggestions.extend(impact_notes)

    detected = detect_skills(resume_text)
    if detected:
        strengths.append(f"Detected {len(detected)} relevant skill keyword(s): {', '.join(detected[:8])}"
                          + ("..." if len(detected) > 8 else "") + ".")
    else:
        suggestions.append("Add a dedicated 'Skills' section listing your technical and soft skills explicitly.")

    if target_job_description.strip():
        match = match_resume_to_job(resume_text, detected, target_job_description, detect_skills(target_job_description))
        keyword_score = match["score"]
        if match["missing_skills"]:
            suggestions.append(
                f"For the '{target_job_title or 'target'}' role, consider adding these keywords if genuinely applicable: "
                + ", ".join(match["missing_skills"][:8]) + "."
            )
        if match["matched_skills"]:
            strengths.append(f"Strong alignment with target role on: {', '.join(match['matched_skills'][:8])}.")
    else:
        # No target JD provided — score keyword richness against the general skill bank
        keyword_score = min(100.0, len(detected) * 8.0)
        if not target_job_description:
            suggestions.append("Tip: paste a target job description to get a role-specific match score.")

    ats_score = round(
        structure_score * 0.30 + readability * 0.20 + keyword_score * 0.30 + impact_score * 0.20, 1
    )

    if not suggestions:
        suggestions.append("Great resume! Keep it updated with your latest achievements.")

    return {
        "ats_score": min(100.0, ats_score),
        "keyword_score": round(keyword_score, 1),
        "readability_score": readability,
        "structure_score": structure_score,
        "strengths": strengths[:8],
        "suggestions": suggestions[:8],
        "detected_skills": detected,
    }
