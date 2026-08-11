"""
Idempotent Production Schema Migration for CareerPilot 'jobs' Table.

Safely inspects the production database table (MySQL, PostgreSQL, or SQLite)
and adds any missing columns, modifies non-nullable columns to allow NULLs (e.g. application_deadline),
and creates missing indexes/unique constraints required by the updated Job SQLAlchemy model
without dropping tables or losing existing data.
"""
import logging
from typing import Dict, Any, List
from sqlalchemy import inspect, text
from app.db.database import engine, Base
import app.models  # Ensures all ORM models are registered

logger = logging.getLogger("careerpilot.migration")

# Mapping of column_name -> SQL type definitions per database dialect
COLUMN_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "source": {
        "mysql": "VARCHAR(50) NOT NULL DEFAULT 'manual'",
        "postgresql": "VARCHAR(50) NOT NULL DEFAULT 'manual'",
        "sqlite": "TEXT NOT NULL DEFAULT 'manual'",
    },
    "source_job_id": {
        "mysql": "VARCHAR(100) NOT NULL DEFAULT ''",
        "postgresql": "VARCHAR(100) NOT NULL DEFAULT ''",
        "sqlite": "TEXT NOT NULL DEFAULT ''",
    },
    "company": {
        "mysql": "VARCHAR(150) NOT NULL DEFAULT 'Company'",
        "postgresql": "VARCHAR(150) NOT NULL DEFAULT 'Company'",
        "sqlite": "TEXT NOT NULL DEFAULT 'Company'",
    },
    "title": {
        "mysql": "VARCHAR(150) NOT NULL DEFAULT ''",
        "postgresql": "VARCHAR(150) NOT NULL DEFAULT ''",
        "sqlite": "TEXT NOT NULL DEFAULT ''",
    },
    "location": {
        "mysql": "VARCHAR(150) NOT NULL DEFAULT 'Remote'",
        "postgresql": "VARCHAR(150) NOT NULL DEFAULT 'Remote'",
        "sqlite": "TEXT NOT NULL DEFAULT 'Remote'",
    },
    "job_type": {
        "mysql": "VARCHAR(50) NOT NULL DEFAULT 'Full-Time'",
        "postgresql": "VARCHAR(50) NOT NULL DEFAULT 'Full-Time'",
        "sqlite": "TEXT NOT NULL DEFAULT 'Full-Time'",
    },
    "description": {
        "mysql": "TEXT",
        "postgresql": "TEXT",
        "sqlite": "TEXT",
    },
    "requirements": {
        "mysql": "TEXT",
        "postgresql": "TEXT",
        "sqlite": "TEXT",
    },
    "skills": {
        "mysql": "JSON",
        "postgresql": "JSONB",
        "sqlite": "TEXT",
    },
    "application_url": {
        "mysql": "VARCHAR(500) NOT NULL DEFAULT ''",
        "postgresql": "VARCHAR(500) NOT NULL DEFAULT ''",
        "sqlite": "TEXT NOT NULL DEFAULT ''",
    },
    "posted_at": {
        "mysql": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "postgresql": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        "sqlite": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "expires_at": {
        "mysql": "DATETIME NULL",
        "postgresql": "TIMESTAMPTZ NULL",
        "sqlite": "TIMESTAMP NULL",
    },
    "application_deadline": {
        "mysql": "DATETIME NULL",
        "postgresql": "TIMESTAMPTZ NULL",
        "sqlite": "TIMESTAMP NULL",
    },
    "last_checked_at": {
        "mysql": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "postgresql": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        "sqlite": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "is_active": {
        "mysql": "BOOLEAN DEFAULT TRUE",
        "postgresql": "BOOLEAN DEFAULT TRUE",
        "sqlite": "BOOLEAN DEFAULT 1",
    },
    "is_remote": {
        "mysql": "BOOLEAN DEFAULT FALSE",
        "postgresql": "BOOLEAN DEFAULT FALSE",
        "sqlite": "BOOLEAN DEFAULT 0",
    },
    "required_skills": {
        "mysql": "JSON",
        "postgresql": "JSONB",
        "sqlite": "TEXT",
    },
    "ctc_or_stipend": {
        "mysql": "VARCHAR(50) DEFAULT ''",
        "postgresql": "VARCHAR(50) DEFAULT ''",
        "sqlite": "TEXT DEFAULT ''",
    },
    "min_cgpa": {
        "mysql": "FLOAT DEFAULT 0.0",
        "postgresql": "FLOAT DEFAULT 0.0",
        "sqlite": "REAL DEFAULT 0.0",
    },
    "eligible_branches": {
        "mysql": "JSON",
        "postgresql": "JSONB",
        "sqlite": "TEXT",
    },
    "posted_by": {
        "mysql": "INT NULL",
        "postgresql": "INTEGER NULL",
        "sqlite": "INTEGER NULL",
    },
    "status": {
        "mysql": "VARCHAR(20) DEFAULT 'open'",
        "postgresql": "VARCHAR(20) DEFAULT 'open'",
        "sqlite": "TEXT DEFAULT 'open'",
    },
    "created_at": {
        "mysql": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "postgresql": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        "sqlite": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
}


def migrate_jobs_schema() -> Dict[str, Any]:
    """
    Idempotently checks the database schema for table 'jobs',
    adds missing columns, alters columns to allow NULLs where optional,
    and creates missing indexes and unique constraints.
    """
    logger.info("Starting jobs schema migration check...")
    added_columns: List[str] = []
    modified_columns: List[str] = []

    try:
        # 1. Ensure table structure is created if non-existent
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        if not inspector.has_table("jobs"):
            logger.info("Table 'jobs' was freshly created by Base.metadata.create_all.")
            return {"status": "success", "added_columns": [], "modified_columns": [], "message": "Fresh table created."}

        existing_columns_map = {col["name"].lower(): col for col in inspector.get_columns("jobs")}
        existing_column_names = set(existing_columns_map.keys())
        dialect_name = engine.dialect.name.lower()
        if dialect_name not in ["mysql", "postgresql", "sqlite"]:
            dialect_name = "mysql"

        with engine.begin() as connection:
            # 2. Add missing columns safely
            for col_name, dialect_defs in COLUMN_DEFINITIONS.items():
                if col_name.lower() not in existing_column_names:
                    col_type_sql = dialect_defs.get(dialect_name, dialect_defs["mysql"])
                    alter_query = f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type_sql}"
                    logger.info(f"Adding missing column '{col_name}' to 'jobs' table: {alter_query}")
                    connection.execute(text(alter_query))
                    added_columns.append(col_name)

            # 3. Modify existing optional columns to ensure they allow NULL values (e.g. application_deadline, expires_at, posted_at)
            nullable_optional_fields = ["application_deadline", "expires_at", "posted_at", "last_checked_at", "posted_by"]
            for col_name in nullable_optional_fields:
                if col_name.lower() in existing_columns_map:
                    col_info = existing_columns_map[col_name.lower()]
                    if col_info.get("nullable") == False:
                        try:
                            if dialect_name == "mysql":
                                connection.execute(text(f"ALTER TABLE jobs MODIFY COLUMN {col_name} DATETIME NULL"))
                            elif dialect_name == "postgresql":
                                connection.execute(text(f"ALTER TABLE jobs ALTER COLUMN {col_name} DROP NOT NULL"))
                            logger.info(f"Modified column '{col_name}' in 'jobs' table to allow NULL values.")
                            modified_columns.append(col_name)
                        except Exception as mod_err:
                            logger.warning(f"Notice modifying column '{col_name}' nullability: {mod_err}")

            # 4. Add missing indexes idempotently
            existing_indexes = {idx["name"].lower() for idx in inspector.get_indexes("jobs") if idx.get("name")}
            
            indexes_to_create = [
                ("ix_jobs_company", "CREATE INDEX ix_jobs_company ON jobs (company)"),
                ("ix_jobs_title", "CREATE INDEX ix_jobs_title ON jobs (title)"),
                ("ix_jobs_location", "CREATE INDEX ix_jobs_location ON jobs (location)"),
                ("ix_jobs_job_type", "CREATE INDEX ix_jobs_job_type ON jobs (job_type)"),
                ("ix_jobs_is_active", "CREATE INDEX ix_jobs_is_active ON jobs (is_active)"),
                ("ix_jobs_is_remote", "CREATE INDEX ix_jobs_is_remote ON jobs (is_remote)"),
                ("ix_jobs_posted_at", "CREATE INDEX ix_jobs_posted_at ON jobs (posted_at)"),
                ("idx_company_active", "CREATE INDEX idx_company_active ON jobs (company, is_active)"),
                ("idx_location_remote", "CREATE INDEX idx_location_remote ON jobs (location, is_remote)"),
                ("idx_active_posted", "CREATE INDEX idx_active_posted ON jobs (is_active, posted_at)"),
            ]

            for idx_name, create_sql in indexes_to_create:
                if idx_name.lower() not in existing_indexes:
                    try:
                        connection.execute(text(create_sql))
                        logger.info(f"Created index: {idx_name}")
                    except Exception as idx_err:
                        logger.warning(f"Notice creating index '{idx_name}': {idx_err}")

            # 5. Add unique constraint uix_source_source_job_id idempotently
            try:
                unique_constraints = {uc["name"].lower() for uc in inspector.get_unique_constraints("jobs") if uc.get("name")}
            except Exception:
                unique_constraints = set()

            if "uix_source_source_job_id" not in unique_constraints and "uix_source_source_job_id" not in existing_indexes:
                try:
                    if dialect_name in ["mysql", "postgresql"]:
                        connection.execute(text("ALTER TABLE jobs ADD CONSTRAINT uix_source_source_job_id UNIQUE (source, source_job_id)"))
                    elif dialect_name == "sqlite":
                        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uix_source_source_job_id ON jobs (source, source_job_id)"))
                    logger.info("Added unique constraint uix_source_source_job_id")
                except Exception as uq_err:
                    logger.warning(f"Notice adding unique constraint uix_source_source_job_id: {uq_err}")

        summary = {
            "status": "success",
            "added_columns": added_columns,
            "modified_columns": modified_columns,
            "count_added": len(added_columns),
            "dialect": dialect_name,
        }
        logger.info(f"Jobs schema migration completed successfully: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Jobs schema migration failed: {e}")
        return {"status": "error", "error": str(e), "added_columns": added_columns, "modified_columns": modified_columns}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = migrate_jobs_schema()
    print(res)
