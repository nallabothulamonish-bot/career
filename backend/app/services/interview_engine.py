
import sys
import os

# Ensure backend root is on sys.path so 'import app...' works from any working directory or terminal
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import random
import re
from typing import List, Dict, Any, Tuple

from app.services.nlp_utils import tokenize, count_action_verbs, count_filler_words, word_count
from app.services import llm_service


QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "Software Engineer": [
        {
            "q": "Walk me through how you would design a scalable URL shortening service.",
            "cat": "technical",
            "topics": ["database", "hashing", "scalability", "cache", "api", "url", "shorten", "system", "design", "redis"]
        },
        {
            "q": "Explain the difference between SQL and NoSQL databases, and when you'd choose each.",
            "cat": "technical",
            "topics": ["sql", "nosql", "schema", "scalability", "consistency", "relational", "document", "mongo", "postgres"]
        },
        {
            "q": "Describe a challenging bug you fixed. What was your step-by-step debugging process?",
            "cat": "behavioral",
            "topics": ["debug", "root cause", "test", "log", "fix", "issue", "solved", "code", "error"]
        },
        {
            "q": "How do you ensure high code quality and maintainability in a team project?",
            "cat": "technical",
            "topics": ["testing", "review", "ci/cd", "lint", "documentation", "unit test", "git", "clean code"]
        },
        {
            "q": "Tell me about a time you disagreed with a teammate on technical architecture. How did you handle it?",
            "cat": "behavioral",
            "topics": ["communication", "compromise", "listen", "team", "resolve", "discussion", "agreed", "decision"]
        },
        {
            "q": "What is time complexity, and why is Big-O notation critical in software performance?",
            "cat": "technical",
            "topics": ["complexity", "algorithm", "big o", "performance", "optimization", "time", "space", "efficiency"]
        },
    ],
    "Data Analyst": [
        {
            "q": "How would you handle missing, corrupted, or inconsistent data in a large dataset?",
            "cat": "technical",
            "topics": ["missing values", "cleaning", "imputation", "outliers", "validation", "pandas", "null", "clean"]
        },
        {
            "q": "Explain the difference between correlation and causation with a real-world example.",
            "cat": "technical",
            "topics": ["correlation", "causation", "statistics", "bias", "experiment", "variables", "data", "relationship"]
        },
        {
            "q": "Describe a time your data insights directly impacted a strategic business decision.",
            "cat": "behavioral",
            "topics": ["insight", "impact", "stakeholder", "decision", "data", "revenue", "results", "dashboard"]
        },
        {
            "q": "What visualization techniques or dashboard metrics would you use to show trends over time?",
            "cat": "technical",
            "topics": ["chart", "trend", "line chart", "dashboard", "visualization", "powerbi", "tableau", "metrics"]
        },
    ],
    "HR/Behavioral": [
        {
            "q": "Tell me about yourself, your technical background, and your career aspirations.",
            "cat": "hr",
            "topics": ["background", "skills", "goal", "experience", "education", "projects", "passionate", "developer"]
        },
        {
            "q": "Why do you want to join our organization, and what makes you a great fit?",
            "cat": "hr",
            "topics": ["company", "value", "goal", "culture", "fit", "growth", "contribution", "team"]
        },
        {
            "q": "Describe a situation where a project failed or missed a deadline. What did you learn?",
            "cat": "behavioral",
            "topics": ["failure", "learn", "improve", "reflect", "accountability", "deadline", "mistake", "adapted"]
        },
        {
            "q": "Where do you see yourself in three to five years professionally?",
            "cat": "hr",
            "topics": ["goal", "growth", "career", "plan", "lead", "senior", "learning", "impact"]
        },
    ],
}

COMMON_ACTION_WORDS = {
    "built", "designed", "created", "implemented", "led", "solved", "managed",
    "fixed", "developed", "handled", "worked", "used", "wrote", "improved",
    "achieved", "analyzed", "deployed", "refactored", "optimized", "tested", "delivered"
}


def get_question_bank_categories() -> List[str]:
    return list(QUESTION_BANK.keys())


def generate_questions(role_category: str, num_questions: int) -> List[Dict[str, Any]]:
    llm_questions = llm_service.generate_interview_questions(role_category, num_questions)
    if llm_questions:
        return [{"question": q, "category": "general"} for q in llm_questions]

    bank = QUESTION_BANK.get(role_category, QUESTION_BANK["Software Engineer"])
    pool = list(bank)
    random.shuffle(pool)
    chosen = pool[:num_questions] if num_questions <= len(pool) else pool
    return [{"question": item["q"], "category": item["cat"], "topics": item.get("topics", [])} for item in chosen]


# Question stop-words to exclude when auto-extracting fallback topics
QUESTION_STOPWORDS = {
    "what", "how", "why", "describe", "explain", "tell", "your", "difference",
    "between", "when", "choose", "each", "would", "which", "handled", "step",
    "process", "time", "walk", "through", "design", "optimize", "handling",
    "ensure", "using", "with", "does", "where", "handling"
}

# Domain concept maps for smart semantic matching
CONCEPT_MAPS: Dict[str, List[str]] = {
    "sql": ["relational", "schema", "postgres", "mysql", "table", "acid", "query", "queries", "join", "index", "indexes", "foreign key", "select"],
    "nosql": ["document", "non-relational", "mongo", "mongodb", "key-value", "redis", "dynamodb", "unstructured", "flexible", "horizontal"],
    "database": ["sql", "nosql", "postgres", "mysql", "mongo", "redis", "schema", "index", "table", "caching", "query"],
    "debug": ["bug", "error", "leak", "log", "logs", "profiler", "trace", "staging", "reproduce", "isolate", "issue", "fix", "fixed", "stack"],
    "scalability": ["scale", "scaling", "cache", "redis", "load balancer", "microservices", "sharding", "horizontal", "latency", "throughput"],
    "optimization": ["index", "indexes", "cache", "latency", "execution plan", "benchmark", "avoid", "profile", "speed", "performance"],
    "behavioral": ["situation", "task", "action", "result", "team", "disagree", "compromise", "learned", "handled", "resolved", "collaborated"]
}


def _find_topics_for_question(role_category: str, question_text: str) -> List[str]:
    q_clean = question_text.strip().lower()
    # Search predefined banks flexibly
    for role, bank in QUESTION_BANK.items():
        for item in bank:
            item_q = item["q"].strip().lower()
            if item_q == q_clean or item_q in q_clean or q_clean in item_q:
                return item.get("topics", [])
    
    # Fallback topic extraction excluding question stop-words
    cleaned = re.sub(r"[^\w\s]", "", q_clean)
    words = [w for w in cleaned.split() if len(w) > 3 and w not in QUESTION_STOPWORDS]
    
    # Inject related concept keywords if matched
    extended_topics = list(words)
    for w in words:
        if w in CONCEPT_MAPS:
            extended_topics.extend(CONCEPT_MAPS[w][:3])
            
    return extended_topics if extended_topics else ["solution", "approach", "implementation"]


def score_answer(question: str, answer: str, category: str, role_category: str = "") -> Dict[str, Any]:
    # Optional LLM hook if configured
    llm_result = llm_service.generate_answer_feedback(question, answer, category)
    if llm_result and "score" in llm_result:
        return {"score": float(llm_result["score"]), "feedback": llm_result.get("feedback", [])}

    feedback: List[str] = []
    score = 0.0
    wc = word_count(answer)
    ans_lower = answer.lower()
    tokens = set(tokenize(answer))

    # 1. Answer Length & Completeness (Max 30 pts)
    if wc >= 20:
        score += 30.0
    elif wc >= 12:
        score += 26.0
    elif wc >= 6:
        score += 20.0
        feedback.append("Good concise answer! Adding 1–2 specific examples or metric outcomes can make it even stronger.")
    else:
        score += 12.0
        feedback.append("Your response is brief — elaborate on your technical approach and outcomes for higher impact.")

    # 2. Topic & Technical Relevance (Max 40 pts)
    topics = _find_topics_for_question(role_category, question)
    
    # Expand topics with concept maps
    expanded_topics = set(topics)
    for t in topics:
        if t in CONCEPT_MAPS:
            expanded_topics.update(CONCEPT_MAPS[t])
            
    if expanded_topics:
        hits = 0
        matched_terms = []
        for t in expanded_topics:
            if any(tok == t or tok in t or t in tok for tok in tokens) or t in ans_lower:
                hits += 1
                matched_terms.append(t)
                
        # Relevance calculation
        relevance_ratio = min(1.0, hits / max(2, min(5, len(topics))))
        topic_score = min(40.0, 24.0 + (relevance_ratio * 16.0))
        score += topic_score

        if hits >= 2 or relevance_ratio >= 0.5:
            feedback.append("Excellent domain relevance! You clearly communicated key technical concepts.")
        elif hits == 1:
            feedback.append("Good technical mention! Try incorporating slightly deeper domain terminology.")
        else:
            feedback.append(f"Consider highlighting core concepts related to: {', '.join(topics[:3])}.")
    else:
        score += 32.0  # Default solid relevance score for open-ended questions

    # 3. Active Ownership Language & Verbs (Max 20 pts)
    action_count = count_action_verbs(answer)
    has_action_words = any(word in ans_lower for word in COMMON_ACTION_WORDS)
    has_first_person = any(fp in ans_lower for fp in ["i ", "my ", "we ", "i'm", "i've", "i'd"])

    if (action_count >= 1 or has_action_words) and has_first_person:
        score += 20.0
        feedback.append("Strong ownership tone! Active phrasing ('I built', 'I analyzed', 'I used') highlights your contribution.")
    elif action_count >= 1 or has_action_words or has_first_person:
        score += 16.0
    else:
        score += 10.0
        feedback.append("Use first-person active verbs ('I implemented', 'I optimized') to showcase personal ownership.")

    # 4. Delivery & Structure (Max 10 pts)
    fillers = count_filler_words(answer)
    if fillers == 0:
        score += 10.0
    elif fillers <= 2:
        score += 7.0
    else:
        score += 3.0
        feedback.append("Try to minimize filler words ('um', 'like', 'basically') for a crisper delivery.")

    # STAR structure bonus for behavioral questions
    if category == "behavioral" or "tell me" in question.lower() or "describe" in question.lower():
        if any(term in ans_lower for term in ["situation", "task", "action", "result", "when i", "outcome", "learned", "fixed"]):
            score = min(100.0, score + 8.0)
            feedback.append("Great structured response following the STAR framework (Situation, Task, Action, Result).")

    # High floor for well-formulated technical answers
    final_score = round(max(50.0, min(100.0, score)), 1)
    if not feedback:
        feedback.append("Well-rounded answer with good technical clarity and structure.")

    return {"score": final_score, "feedback": feedback[:4]}


def summarize_session(answers: List[Dict[str, Any]]) -> Tuple[float, str]:
    if not answers:
        return 0.0, "No answers submitted."
    avg = sum(a["score"] for a in answers) / len(answers)
    if avg >= 80:
        summary = "Outstanding interview performance! You demonstrated clear technical depth, ownership language, and structured responses."
    elif avg >= 65:
        summary = "Solid performance! You communicated your points well with good domain coverage. Review individual question feedback for minor tweaks."
    else:
        summary = "Good effort! Focus on expanding your answers with concrete examples, active verbs, and key technical terms to raise your score."
    return round(avg, 1), summary


if __name__ == "__main__":
    test_res = score_answer(
        "Explain the difference between SQL and NoSQL databases",
        "SQL is relational with fixed schemas while NoSQL is document based.",
        "technical",
        "Software Engineer"
    )
    print("Interview Engine loaded and tested successfully!")
    print("Test Score:", test_res["score"])
    print("Test Feedback:", test_res["feedback"])

