"""
Demo data seeder. Run with: python -m app.seed.seed
Creates 1 placement officer, 3 students (with resumes/skills), and 3 open jobs.
Requires the MySQL database referenced in DATABASE_URL to already exist.
"""
from datetime import datetime, timedelta

from app.db.database import SessionLocal, Base, engine
from app.models.user import User, RoleEnum
from app.models.student_profile import StudentProfile
from app.models.job import Job
from app.models.application import Application
from app.models.resume_analysis import ResumeAnalysis
from app.models.mock_interview import MockInterviewSession, MockInterviewAnswer
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    try:
        print("Clearing existing data...")
        db.query(MockInterviewAnswer).delete()
        db.query(MockInterviewSession).delete()
        db.query(ResumeAnalysis).delete()
        db.query(Application).delete()
        db.query(Job).delete()
        db.query(StudentProfile).delete()
        db.query(User).delete()
        db.commit()

        officer = User(
            name="Priya Sharma", email="officer@college.edu",
            password_hash=hash_password("password123"), role=RoleEnum.placement_officer,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)

        students_data = [
            dict(name="Arjun Rao", email="arjun@college.edu", branch="Computer Science", cgpa=8.7,
                 skills=["javascript", "react", "node.js", "mongodb", "express", "git"],
                 resume="Final year Computer Science student with experience building full stack web "
                        "applications using React, Node.js, Express and MongoDB. Built a placement "
                        "management system as a capstone project. Skills: JavaScript, React, Node.js, "
                        "MongoDB, Express, Git.\n\nExperience:\n- Built and deployed 3 full stack projects\n"
                        "- Reduced page load time by 35% through code splitting\n\nEducation:\nB.Tech "
                        "Computer Science, XYZ University, 2026"),
            dict(name="Sneha Iyer", email="sneha@college.edu", branch="Computer Science", cgpa=9.1,
                 skills=["python", "machine learning", "pandas", "numpy", "sql", "tensorflow"],
                 resume="Computer Science student specializing in Machine Learning and Data Science. "
                        "Skills: Python, TensorFlow, Pandas, NumPy, SQL.\n\nProjects:\n- Built a predictive "
                        "model improving forecast accuracy by 22%\n- Published a research paper on "
                        "predictive analytics\n\nEducation:\nB.Tech Computer Science, XYZ University, 2026"),
            dict(name="Karan Mehta", email="karan@college.edu", branch="Electronics", cgpa=7.5,
                 skills=["c++", "embedded systems", "arduino", "circuit design"],
                 resume="Electronics engineering student with hands-on experience in embedded systems, "
                        "Arduino based projects and circuit design.\n\nExperience:\n- Interned at a "
                        "hardware startup building IoT prototypes\n- Designed 5+ circuit boards for "
                        "coursework projects\n\nEducation:\nB.Tech Electronics, XYZ University, 2026"),
        ]

        for s in students_data:
            u = User(name=s["name"], email=s["email"], password_hash=hash_password("password123"), role=RoleEnum.student)
            db.add(u)
            db.commit()
            db.refresh(u)
            db.add(StudentProfile(
                user_id=u.id, branch=s["branch"], cgpa=s["cgpa"], graduation_year=2026,
                skills=s["skills"], resume_text=s["resume"], roll_number=f"R-{u.id:04d}",
            ))
        db.commit()

        jobs_data = [
            dict(
                title="Software Engineer (L3 Campus Drive)",
                company="Google",
                description="Google Campus Recruitment 2026: Looking for talented final-year students with exceptional algorithmic problem-solving skills in C++, Python, or Java. You will work on core Google infrastructure, search, and cloud products. Selection Process: Online Coding Round -> 3 Technical Rounds -> HR Round. CTC: ₹28,000,000 / year (28 LPA).",
                required_skills=["c++", "python", "data structures", "algorithms", "system design", "git"],
                job_type="Full-Time",
                min_cgpa=8.0,
                eligible_branches=["Computer Science", "Information Technology", "Electronics"],
                deadline_days=15,
            ),
            dict(
                title="Software Development Engineer (SDE-1)",
                company="Microsoft",
                description="Microsoft University Hiring: Join Microsoft Azure and Office 365 engineering teams! Strong knowledge of Data Structures, Object-Oriented Programming (C++/Java/C#), and Database Management Systems required. Selection Process: Online Aptitude & Coding Test -> 2 Technical Interviews -> AA Round. CTC: ₹24,000,000 / year (24 LPA).",
                required_skills=["c++", "java", "data structures", "algorithms", "sql", "oop"],
                job_type="Full-Time",
                min_cgpa=7.5,
                eligible_branches=["Computer Science", "Information Technology", "Electronics"],
                deadline_days=12,
            ),
            dict(
                title="Graduate Cloud & Systems Engineer",
                company="Amazon AWS",
                description="Amazon Web Services (AWS) Campus Recruitment: Seeking proactive engineering graduates to build next-generation cloud infrastructure. Key skills include Linux, Networking fundamentals, Python scripting, and Java. CTC: ₹22,000,000 / year (22 LPA).",
                required_skills=["python", "java", "aws", "networking", "linux", "git"],
                job_type="Full-Time",
                min_cgpa=7.5,
                eligible_branches=["Computer Science", "Information Technology", "Electronics", "Electrical"],
                deadline_days=18,
            ),
            dict(
                title="Digital Software Developer Drive",
                company="TCS Digital",
                description="Tata Consultancy Services (TCS) Digital Recruitment Drive: Elite hiring stream for high-performing graduates. Roles involve building AI/ML solutions, cloud microservices, and enterprise applications. Selection Process: TCS NQT (Numerical, Logical, Verbal + Advanced Coding) -> Interview. CTC: ₹750,000 / year (7.5 LPA).",
                required_skills=["java", "python", "sql", "javascript", "react", "html"],
                job_type="Full-Time",
                min_cgpa=6.5,
                eligible_branches=["Computer Science", "Information Technology", "Electronics", "Electrical", "Mechanical"],
                deadline_days=25,
            ),
            dict(
                title="Specialist Programmer (Power Programmer)",
                company="Infosys",
                description="Infosys Power Programmer Drive: Hiring high-caliber developers skilled in competitive programming, algorithms, Python, Java, and modern web stack. Selection Process: HackWithInfy / InfyTQ -> Technical Interview. CTC: ₹950,000 / year (9.5 LPA).",
                required_skills=["python", "java", "c++", "data structures", "sql", "git"],
                job_type="Full-Time",
                min_cgpa=7.0,
                eligible_branches=["Computer Science", "Information Technology", "Electronics"],
                deadline_days=20,
            ),
            dict(
                title="Software Engineering Associate",
                company="J.P. Morgan & Co.",
                description="J.P. Morgan Global Technology Infrastructure Drive: Develop enterprise financial technology platforms, low-latency algorithms, and web applications using React, Python, and SQL. Selection Process: CodeVue Online Assessment -> Hackathon -> 2 Interview Rounds. CTC: ₹19,500,000 / year (19.5 LPA).",
                required_skills=["python", "java", "react", "sql", "data structures", "javascript"],
                job_type="Full-Time",
                min_cgpa=8.0,
                eligible_branches=["Computer Science", "Information Technology", "Electronics"],
                deadline_days=14,
            ),
            dict(
                title="Technology Consulting Analyst",
                company="Deloitte",
                description="Deloitte US-India Campus Drive: Technology analysts work with fortune 500 clients in cloud transformation, data analytics, and software implementation. Requires strong SQL, Python, problem-solving, and communication skills. CTC: ₹1,000,000 / year (10 LPA).",
                required_skills=["python", "sql", "analytics", "cloud", "communication"],
                job_type="Full-Time",
                min_cgpa=6.5,
                eligible_branches=["Computer Science", "Information Technology", "Electronics", "Electrical", "Mechanical"],
                deadline_days=10,
            ),
        ]

        for j in jobs_data:
            db.add(Job(
                title=j["title"], company=j["company"], description=j["description"],
                required_skills=j["required_skills"], job_type=j["job_type"], min_cgpa=j["min_cgpa"],
                eligible_branches=j["eligible_branches"],
                application_deadline=datetime.utcnow() + timedelta(days=j["deadline_days"]),
                posted_by=officer.id,
            ))
        db.commit()


        print("Seed complete!")
        print("Placement Officer login: officer@college.edu / password123")
        print("Student logins: arjun@college.edu / sneha@college.edu / karan@college.edu (password123)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
