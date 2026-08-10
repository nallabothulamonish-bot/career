# CareerPilot AI — Career & Placement Management Platform (v2)

A full-stack, production-style platform for colleges to manage placement drives,
with AI-powered resume↔job matching, an ATS-style **Resume Analyzer**, an
**AI Mock Interview simulator**, and a career assistant chatbot.

## Tech Stack
| Layer | Tech |
|---|---|
| Frontend | React.js, Vite, HTML5, CSS3 (Tailwind), JavaScript (ES2022), Framer Motion |
| Backend | Python, FastAPI, SQLAlchemy ORM |
| Database | MySQL 8 |
| AI / ML / NLP | scikit-learn (TF-IDF + cosine similarity), custom NLP heuristics, optional LLM (Anthropic API) hook |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Tooling | Git & GitHub |
| Deployment | Vercel (frontend), Render (backend + MySQL) |

## Why this stack
- **FastAPI** gives async-ready, auto-documented (`/docs`) REST APIs with Pydantic validation.
- **scikit-learn TF-IDF + cosine similarity** is a real, explainable ML technique for
  resume↔JD matching — no black-box dependency, runs offline, and is fast enough for
  real-time scoring on every application.
- **MySQL** with SQLAlchemy JSON columns stores flexible skill/education lists while
  keeping relational integrity (foreign keys, unique constraints) for applications.
- **Optional LLM hook** (`services/llm_service.py`) lets you flip on Claude-generated
  interview questions/feedback by just adding `ANTHROPIC_API_KEY` — with automatic,
  invisible fallback to the rule-based engine if it's not set or a call fails.

## Features

### For Students
- Profile builder (skills, CGPA, branch, resume text)
- Browse & apply to job drives — **instant AI match score** (0–100%) with matched/missing skills
- Track applications through the pipeline
- **🆕 AI Resume Analyzer** — ATS score, structure/readability/keyword sub-scores, strengths & prioritized suggestions, optional role-specific keyword-gap analysis
- **🆕 AI Mock Interview** — pick a role (Software Engineer / Data Analyst / HR-Behavioral), answer 5 questions, get per-answer AI feedback (relevance, action-language, STAR structure for behavioral) + an overall session score and summary
- Career assistant chatbot (open drives, eligibility, application status, resume tips, mock interview pointers — powered by live DB queries)

### For Placement Officers
- Post/edit/delete job drives with eligibility rules (min CGPA, branches)
- View applicants **auto-ranked by AI match score**, with matched/missing skill breakdown
- Move applicants through the pipeline (Applied → Shortlisted → Interview → Selected/Rejected)
- Analytics dashboard: total students, placement rate, open drives, avg match score, applications-by-status chart

### UI/UX
- Framer Motion page transitions, staggered card reveals, animated circular score rings, gradient hero backgrounds, glassmorphism navbar, hover micro-interactions throughout.

## Project Structure
```
careerpilot/
├── backend/
│   └── app/
│       ├── core/          config.py, security.py (JWT/bcrypt), deps.py (auth guards)
│       ├── db/database.py  SQLAlchemy engine/session
│       ├── models/         User, StudentProfile, Job, Application, ResumeAnalysis,
│       │                   MockInterviewSession, MockInterviewAnswer
│       ├── schemas/        Pydantic request/response models
│       ├── routers/        auth, students, jobs, applications, resume, interview, chatbot
│       ├── services/        <-- AI/ML/NLP logic lives here
│       │    ├── nlp_utils.py         tokenizer, skill bank, action-verb/filler detection
│       │    ├── resume_matcher.py    TF-IDF + cosine similarity (sklearn)
│       │    ├── resume_analyzer.py   ATS scoring engine (structure/readability/keywords/impact)
│       │    ├── interview_engine.py  question bank + rule-based answer scoring (STAR-aware)
│       │    ├── chatbot_engine.py    intent classifier + live DB-aware replies
│       │    └── llm_service.py       optional Anthropic API wrapper w/ graceful fallback
│       └── seed/seed.py    demo data
└── frontend/
    └── src/
        ├── pages/    Login, Register, StudentDashboard, PlacementDashboard, Profile,
        │             ApplicantsPage, ResumeAnalyzer, MockInterview
        ├── components/ Navbar, JobCard, JobForm, ChatbotWidget, MatchScoreBadge,
        │               CircularProgress, PageTransition, ProtectedRoute
        ├── context/AuthContext.jsx
        └── api/axios.js
```

## Setup & Run Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8+ running locally (or a cloud instance)

### 1. Database
```sql
CREATE DATABASE careerpilot CHARACTER SET utf8mb4;
```

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit DATABASE_URL / JWT_SECRET
uvicorn app.main:app --reload --port 8000
# in a second terminal, once the server has created tables:
python -m app.seed.seed     # optional demo data
```
API docs available at `http://localhost:8000/docs` (FastAPI auto-generated Swagger UI).

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://localhost:8000/api
npm run dev                  # http://localhost:5173
```

### Demo Logins (after `python -m app.seed.seed`)
| Role | Email | Password |
|---|---|---|
| Placement Officer | officer@college.edu | password123 |
| Student | arjun@college.edu | password123 |
| Student | sneha@college.edu | password123 |
| Student | karan@college.edu | password123 |

## How the AI Features Work

**1. Resume ↔ Job Matching** (`resume_matcher.py`)
TF-IDF vectors (scikit-learn) + cosine similarity for textual relevance, blended
60/40 with exact required-skill coverage → single 0–100% score shown on every application.

**2. Resume Analyzer** (`resume_analyzer.py`)
Four weighted sub-scores — Structure (30%): section-presence regex checks;
Readability (20%): word/sentence-length + bullet-point heuristics; Keyword
Match (30%): same TF-IDF engine against a target JD (or general skill-bank
richness if no JD given); Impact (20%): action-verb density + quantified
achievement detection — combined into one ATS score with prioritized,
human-readable suggestions.

**3. Mock Interview** (`interview_engine.py`)
Curated question bank per role (technical/behavioral/HR), each tagged with
expected topic keywords. Answers are scored on: length/completeness, topic
relevance, action-verb usage, filler-word penalty, and — for behavioral
questions — STAR-structure detection. Session-level summary is generated from
the average.

**4. Optional LLM upgrade** (`llm_service.py`)
Set `ANTHROPIC_API_KEY` in `backend/.env` to have interview questions and
answer feedback generated by Claude instead of the rule-based engine — no
code changes needed, and it silently falls back if the key is missing or a
call fails.

**5. Chatbot** (`chatbot_engine.py`)
Keyword-scored intent classifier that queries MySQL live (via SQLAlchemy) for
personalized answers scoped to the logged-in student.

## Deployment
See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for step-by-step Render (backend + MySQL)
and Vercel (frontend) instructions, plus the Git/GitHub workflow.

## Suggested Next Steps
- PDF resume upload + text extraction (`pdf-parse` / `pdfplumber`) instead of paste-only
- Voice-based mock interview (Web Speech API) with tone/pace analysis
- Email notifications on status change
- Admin analytics export (CSV/PDF reports)
- Rate-limit the LLM calls if `ANTHROPIC_API_KEY` is enabled at scale
