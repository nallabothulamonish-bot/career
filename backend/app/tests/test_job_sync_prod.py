import unittest
from unittest.mock import MagicMock, patch
from app.services.job_sync import get_sync_status, run_job_sync_pipeline, auto_sync_on_startup, SYNC_STATUS, SYNC_LOCK


class TestJobSyncProduction(unittest.TestCase):
    def setUp(self):
        self.db_mock = MagicMock()

    def test_sync_status_schema(self):
        self.db_mock.query().filter().count.return_value = 4341
        self.db_mock.query().filter().order_by().first.return_value = None

        status = get_sync_status(self.db_mock)
        self.assertIn("last_sync", status)
        self.assertIn("active_jobs", status)
        self.assertIn("companies", status)
        self.assertIn("sync_running", status)
        self.assertEqual(status["active_jobs"], 4341)
        self.assertIsInstance(status["sync_running"], bool)

    @patch("app.services.job_sync.run_job_sync_pipeline")
    @patch("app.services.job_sync.SessionLocal")
    def test_auto_sync_on_startup_when_zero_jobs(self, mock_session, mock_run_pipeline):
        db_inst = MagicMock()
        db_inst.query().filter().count.return_value = 0
        mock_session.return_value = db_inst

        auto_sync_on_startup()
        mock_run_pipeline.assert_called_once()

    @patch("app.services.job_sync.run_job_sync_pipeline")
    @patch("app.services.job_sync.SessionLocal")
    def test_auto_sync_on_startup_when_jobs_exist(self, mock_session, mock_run_pipeline):
        db_inst = MagicMock()
        db_inst.query().filter().count.return_value = 500
        mock_session.return_value = db_inst

        auto_sync_on_startup()
        mock_run_pipeline.assert_not_called()

    def test_concurrency_lock(self):
        # Simulate lock held
        acquired = SYNC_LOCK.acquire(blocking=False)
        self.assertTrue(acquired)

        try:
            res = run_job_sync_pipeline()
            self.assertEqual(res.get("status"), "skipped")
            self.assertTrue(res.get("sync_running"))
        finally:
            SYNC_LOCK.release()


if __name__ == "__main__":
    unittest.main()
