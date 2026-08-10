-- Reference schema (auto-created by SQLAlchemy on startup via Base.metadata.create_all()).
-- Run this manually only if you prefer to provision the schema yourself.
-- Requires MySQL 8.0+ (for native JSON column support).

CREATE DATABASE IF NOT EXISTS careerpilot CHARACTER SET utf8mb4;
USE careerpilot;

-- Tables below are illustrative; SQLAlchemy models in app/models/*.py are the source of truth.
-- users, student_profiles, jobs, applications, resume_analyses,
-- mock_interview_sessions, mock_interview_answers
