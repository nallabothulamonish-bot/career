import unittest
from unittest.mock import MagicMock
from app.services.chatbot_engine import (
    _detect_intent_and_entities,
    get_chatbot_reply,
)


class TestChatbotEngine(unittest.TestCase):
    def setUp(self):
        self.db_mock = MagicMock()

    def test_intent_detection(self):
        intent, _ = _detect_intent_and_entities("Show Stripe jobs", self.db_mock)
        self.assertEqual(intent, "COMPANY_SEARCH")

        intent, _ = _detect_intent_and_entities("Show me software jobs in Bangalore", self.db_mock)
        self.assertIn(intent, ["LOCATION_SEARCH", "JOB_SEARCH"])

        intent, _ = _detect_intent_and_entities("Show me internships in Hyderabad", self.db_mock)
        self.assertEqual(intent, "INTERNSHIP_SEARCH")

        intent, _ = _detect_intent_and_entities("What jobs match my skills?", self.db_mock)
        self.assertEqual(intent, "RECOMMENDATIONS")

        intent, _ = _detect_intent_and_entities("What is my application status?", self.db_mock)
        self.assertEqual(intent, "APPLICATION_STATUS")

        intent, _ = _detect_intent_and_entities("Give me resume tips", self.db_mock)
        self.assertEqual(intent, "RESUME_HELP")

        intent, _ = _detect_intent_and_entities("Help me prepare for a Python interview", self.db_mock)
        self.assertEqual(intent, "INTERVIEW_HELP")


if __name__ == "__main__":
    unittest.main()
