"""
Shared NLP utilities used across the resume matcher, resume analyzer,
and mock interview feedback engine. Pure scikit-learn + regex based —
no heavyweight model downloads required (works fully offline).
"""
import re
from collections import Counter

STOPWORDS = set("""
a an the and or but if in on at to for of with by is are was were be been
being this that these those it as from which who whom will would should
can could may might shall must have has had do does did not no we you
your i he she they them our us their its about into than then so such
also using use used etc all any some more most other into over under
""".split())

# A reasonably broad technical/soft-skill keyword bank used for skill
# detection in free-text resumes when the user hasn't tagged skills explicitly.
SKILL_BANK = [
    "python", "java", "javascript", "typescript", "c++", "c#", "react", "angular", "vue",
    "node.js", "express", "django", "flask", "fastapi", "spring boot", "sql", "mysql",
    "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "github", "ci/cd", "html", "css", "tailwind", "bootstrap", "rest api",
    "graphql", "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "data analysis",
    "data visualization", "power bi", "tableau", "excel", "linux", "agile", "scrum",
    "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    "project management", "figma", "ui/ux", "testing", "selenium", "jenkins",
]

ACTION_VERBS = {
    "led", "built", "designed", "developed", "implemented", "created", "improved",
    "increased", "reduced", "optimized", "launched", "managed", "architected",
    "automated", "delivered", "achieved", "spearheaded", "collaborated", "mentored",
    "analyzed", "streamlined", "engineered", "used", "avoided", "indexed",
    "reproduced", "isolated", "profiled", "benchmarked", "configured", "resolved", "fixed",
}

FILLER_WORDS = {"um", "uh", "like", "basically", "actually", "literally", "sort of", "kind of", "you know"}


def tokenize(text: str) -> list[str]:
    # Replace punctuation with spaces so "relational.NoSQL" becomes "relational NoSQL"
    cleaned = re.sub(r"[^\w\s+#.]", " ", (text or "").lower())
    # Separate trailing/leading dots/commas from words unless part of C++ or Node.js or #
    raw_tokens = re.findall(r"[a-zA-Z0-9+#.]+", cleaned)
    tokens = []
    for t in raw_tokens:
        t_strip = t.strip(".")
        if t_strip:
            tokens.append(t_strip)
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]



def detect_skills(text: str) -> list[str]:
    lower = (text or "").lower()
    return sorted({skill for skill in SKILL_BANK if skill in lower})


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def sentence_count(text: str) -> int:
    sentences = re.split(r"[.!?]+", text or "")
    return len([s for s in sentences if s.strip()])


def count_action_verbs(text: str) -> int:
    tokens = set(tokenize(text))
    return len(tokens & ACTION_VERBS)


def count_filler_words(text: str) -> int:
    lower = (text or "").lower()
    return sum(lower.count(f) for f in FILLER_WORDS)
