"""
Thin, optional wrapper around the Anthropic API.

If ANTHROPIC_API_KEY is not set, every function here returns None and callers
fall back to the rule-based NLP engines (interview_engine.py, resume_analyzer.py).
This keeps the whole platform fully functional with zero external dependencies,
while letting you flip on real LLM-generated questions/feedback by just adding a key.
"""
from app.core.config import settings

_client = None
if settings.ANTHROPIC_API_KEY:
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    except Exception:
        _client = None


def is_available() -> bool:
    return _client is not None


def generate_interview_questions(role_category: str, num_questions: int) -> list[str] | None:
    if not _client:
        return None
    try:
        resp = _client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    f"Generate {num_questions} realistic mock interview questions for a "
                    f"'{role_category}' candidate. Return ONLY a numbered list, one question per line, "
                    f"no preamble."
                ),
            }],
        )
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
        lines = [re_line.split(".", 1)[-1].strip() for re_line in text.strip().split("\n") if re_line.strip()]
        return [l for l in lines if l][:num_questions] or None
    except Exception:
        return None


def generate_answer_feedback(question: str, answer: str, category: str) -> dict | None:
    if not _client:
        return None
    try:
        resp = _client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"You are an interview coach. Question ({category}): {question}\n"
                    f"Candidate's answer: {answer}\n\n"
                    "Score the answer 0-100 and give 2-3 short, specific improvement tips. "
                    "Respond ONLY as JSON: {\"score\": <int>, \"feedback\": [\"tip1\", \"tip2\"]}"
                ),
            }],
        )
        import json
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
        return json.loads(text.strip().strip("`").replace("json\n", "", 1))
    except Exception:
        return None
