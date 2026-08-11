import json
from app.db.database import SessionLocal
from app.models.user import User
from app.services.chatbot_engine import get_chatbot_reply

def main():
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.role == "student").first()
        student_id = int(student.id) if student and student.id is not None else None

        print("=== TEST 1: 'Show Stripe jobs' ===")
        res1 = get_chatbot_reply("Show Stripe jobs", db, user_id=student_id)
        print(json.dumps(res1.model_dump(), indent=2))

        print("\n=== TEST 2: 'What jobs match my skills?' ===")
        res2 = get_chatbot_reply("What jobs match my skills?", db, user_id=student_id)
        print(json.dumps(res2.model_dump(), indent=2))

    finally:
        db.close()

if __name__ == "__main__":
    main()
