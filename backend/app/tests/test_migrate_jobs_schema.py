import unittest
from sqlalchemy import inspect
from app.db.database import engine
from app.db.migrate_jobs_schema import migrate_jobs_schema, COLUMN_DEFINITIONS


class TestJobsSchemaMigration(unittest.TestCase):
    def test_migration_execution_and_idempotency(self):
        # 1. Run migration first time
        res1 = migrate_jobs_schema()
        self.assertEqual(res1["status"], "success")

        # Verify all required columns exist in jobs table
        inspector = inspect(engine)
        self.assertTrue(inspector.has_table("jobs"))
        existing_cols = {col["name"].lower() for col in inspector.get_columns("jobs")}

        for col_name in COLUMN_DEFINITIONS.keys():
            self.assertIn(
                col_name.lower(),
                existing_cols,
                f"Column '{col_name}' should exist in jobs table after migration"
            )

        # 2. Run migration a second time (Idempotency test)
        res2 = migrate_jobs_schema()
        self.assertEqual(res2["status"], "success")
        self.assertEqual(
            res2.get("count_added", 0),
            0,
            "Second migration run should add 0 columns (idempotent)"
        )


if __name__ == "__main__":
    unittest.main()
