import unittest
from unittest.mock import MagicMock
from app.models.job import Job
from app.models.student_profile import StudentProfile
from app.services.recommendation_engine import compute_job_match, compute_job_match_detailed


class TestRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.student = StudentProfile(
            branch="Computer Science",
            cgpa=8.5,
            skills=["python", "react", "sql", "git"],
            resume_text="Computer Science student with experience building React web applications and Python scripting."
        )

    def test_intern_ranks_above_director(self):
        intern_job = Job(
            id=1,
            title="Software Engineering Intern",
            company="Tech Corp",
            location="Bengaluru",
            job_type="Internship",
            skills=["python", "react"],
            description="Looking for Software Engineering Interns with Python and React skills.",
            is_active=True
        )

        director_job = Job(
            id=2,
            title="Director, Strategic Partnerships",
            company="Gitlab",
            location="Remote, US",
            job_type="Full-Time",
            skills=[],
            description="Director level role leading global strategic partnerships and account teams.",
            is_active=True
        )

        intern_score, intern_reasons = compute_job_match(self.student, intern_job)
        director_score, director_reasons = compute_job_match(self.student, director_job)

        self.assertGreater(intern_score, director_score, f"Intern score ({intern_score}) should be > Director score ({director_score})")
        self.assertLess(director_score, 50.0, f"Director score ({director_score}) should be heavily penalized")

    def test_junior_dev_ranks_above_senior_architect(self):
        junior_job = Job(
            id=3,
            title="Junior Software Developer",
            company="Dev Solutions",
            location="Hyderabad",
            job_type="Full-Time",
            skills=["python", "sql"],
            description="Junior developer role for Computer Science fresh graduates.",
            is_active=True
        )

        architect_job = Job(
            id=4,
            title="Senior Solutions Architect",
            company="Enterprise Systems",
            location="Remote",
            job_type="Full-Time",
            skills=["aws", "architecture"],
            description="Senior Architect requiring 10+ years experience leading enterprise cloud architecture.",
            is_active=True
        )

        junior_score, _ = compute_job_match(self.student, junior_job)
        architect_score, _ = compute_job_match(self.student, architect_job)

        self.assertGreater(junior_score, architect_score, f"Junior Dev ({junior_score}) should rank > Senior Architect ({architect_score})")

    def test_unrelated_sales_role_low_score(self):
        sales_job = Job(
            id=5,
            title="Account Executive, Sales",
            company="Sales Corp",
            location="Mumbai",
            job_type="Full-Time",
            skills=["sales", "cold calling"],
            description="Outbound sales and client acquisition account executive.",
            is_active=True
        )

        sales_score, _ = compute_job_match(self.student, sales_job)
        detail = compute_job_match_detailed(self.student, sales_job)

        self.assertLess(sales_score, 45.0, f"Sales role score ({sales_score}) should be low for CSE student")
        self.assertTrue(any("Sales" in r for r in detail["mismatch_reasons"]))


if __name__ == "__main__":
    unittest.main()
