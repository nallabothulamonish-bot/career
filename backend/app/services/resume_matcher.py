"""
AI Resume <-> Job Description matcher.
Uses scikit-learn's TfidfVectorizer + cosine_similarity (real ML/NLP technique)
for textual relevance, blended with exact required-skill coverage for precision.
Runs fully offline — no external API calls, no model downloads.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.nlp_utils import STOPWORDS


def _text_similarity(resume_text: str, job_text: str) -> float:
    docs = [resume_text or "", job_text or ""]
    if not any(d.strip() for d in docs):
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), token_pattern=r"[a-zA-Z0-9+#.]+")
        tfidf_matrix = vectorizer.fit_transform(docs)
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(sim)
    except ValueError:
        # e.g. empty vocabulary after stopword removal
        return 0.0


def match_resume_to_job(
    resume_text: str,
    candidate_skills: list[str],
    job_description: str,
    required_skills: list[str],
) -> dict:
    combined_resume = f"{resume_text or ''} {' '.join(candidate_skills or [])}"
    text_similarity = _text_similarity(combined_resume, job_description)

    normalized_required = [s.lower().strip() for s in (required_skills or [])]
    resume_lower = (resume_text or "").lower()
    skills_lower = [s.lower().strip() for s in (candidate_skills or [])]

    matched, missing = [], []
    for skill in normalized_required:
        if skill in skills_lower or skill in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    skill_coverage = (len(matched) / len(normalized_required)) if normalized_required else 0.5

    final_score = skill_coverage * 0.6 + text_similarity * 0.4

    return {
        "score": round(final_score * 100, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "text_similarity": round(text_similarity * 100, 1),
        "skill_coverage": round(skill_coverage * 100, 1),
    }
