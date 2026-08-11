import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.db.database import SessionLocal
import app.models  # noqa: F401
from app.models import Job
from app.services.nlp_utils import detect_skills
from app.services.cache_service import cache_service

logger = logging.getLogger("careerpilot.job_sync")

# Verified, legitimate official company boards for Greenhouse and Lever
DEFAULT_GREENHOUSE_BOARDS = [
    "cloudflare", "gitlab", "stripe", "figma", "canonical",
    "elastic", "mongodb", "pinterest", "airbnb", "okta",
    "databricks", "reddit", "dropbox"
]
DEFAULT_LEVER_BOARDS = ["palantir", "spotify", "cred"]

INDIA_LOCATION_KEYWORDS = [
    "india", "bengaluru", "bangalore", "hyderabad", "chennai", "pune",
    "mumbai", "gurugram", "gurgaon", "noida", "delhi"
]


def _clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", html_text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:5000]


def _is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    clean_url = url.strip().lower()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        return False
    if any(bad in clean_url for bad in ["javascript:", "example.com", "localhost", "#", "leverdemo"]):
        return False
    return True


def _determine_job_type(title: str, text: str) -> str:
    combined = (title + " " + text).lower()
    if "intern" in combined or "co-op" in combined:
        return "Internship"
    if "contract" in combined or "freelance" in combined or "temporary" in combined:
        return "Contract"
    if "part-time" in combined or "part time" in combined:
        return "Part-Time"
    return "Full-Time"


async def fetch_greenhouse_jobs(board: str) -> List[Dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    parsed_jobs = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Greenhouse board '{board}' returned status {resp.status_code}")
                return []
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            for item in raw_jobs:
                job_id = str(item.get("id", "")).strip()
                title = item.get("title", "").strip()
                app_url = item.get("absolute_url", "").strip()

                if not job_id or not title or not _is_valid_url(app_url):
                    continue

                location = (item.get("location", {}) or {}).get("name", "Remote").strip()
                html_content = item.get("content", "")
                clean_desc = _clean_html(html_content)

                is_remote = "remote" in location.lower() or "remote" in title.lower() or "work from home" in clean_desc.lower()
                job_type = _determine_job_type(title, clean_desc)
                skills = detect_skills(title + " " + clean_desc)

                parsed_jobs.append({
                    "source": "greenhouse",
                    "source_job_id": job_id[:95],
                    "company": board.capitalize()[:95],
                    "title": title[:95],
                    "location": (location if location else "Remote")[:95],
                    "job_type": job_type[:45],
                    "description": clean_desc if clean_desc else title,
                    "requirements": "See official Greenhouse posting for full details.",
                    "skills": skills,
                    "application_url": app_url[:490],
                    "is_remote": is_remote,
                    "posted_at": datetime.now(timezone.utc),
                })

    except Exception as e:
        logger.error(f"Error fetching Greenhouse board '{board}': {e}")
    return parsed_jobs


async def fetch_lever_jobs(company: str) -> List[Dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    parsed_jobs = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Lever board '{company}' returned status {resp.status_code}")
                return []
            raw_jobs = resp.json()
            if not isinstance(raw_jobs, list):
                return []
            for item in raw_jobs:
                job_id = str(item.get("id", "")).strip()
                title = item.get("text", "").strip()
                app_url = item.get("hostedUrl", "") or item.get("applyUrl", "")
                app_url = str(app_url).strip()

                if not job_id or not title or not _is_valid_url(app_url):
                    continue

                cats = item.get("categories", {}) or {}
                location = cats.get("location", "Remote") or "Remote"
                commitment = cats.get("commitment", "Full-Time") or "Full-Time"
                desc_html = item.get("descriptionHtml", "") or ""
                clean_desc = _clean_html(desc_html)

                is_remote = "remote" in location.lower() or "remote" in title.lower() or "work from home" in clean_desc.lower()
                job_type = _determine_job_type(title + " " + commitment, clean_desc)
                skills = detect_skills(title + " " + clean_desc)

                parsed_jobs.append({
                    "source": "lever",
                    "source_job_id": job_id[:95],
                    "company": company.capitalize()[:95],
                    "title": title[:95],
                    "location": (location if location else "Remote")[:95],
                    "job_type": job_type[:45],
                    "description": clean_desc if clean_desc else title,
                    "requirements": "See official Lever posting for full details.",
                    "skills": skills,
                    "application_url": app_url[:490],
                    "is_remote": is_remote,
                    "posted_at": datetime.now(timezone.utc),
                })

    except Exception as e:
        logger.error(f"Error fetching Lever board '{company}': {e}")
    return parsed_jobs


async def fetch_all_external_jobs() -> List[Dict[str, Any]]:
    all_jobs = []

    # Configured boards or defaults
    configured = [b.strip().lower() for b in settings.DEFAULT_JOB_BOARDS.split(",") if b.strip() and b.strip().lower() != "leverdemo"]
    gh_boards = [b for b in configured if b in DEFAULT_GREENHOUSE_BOARDS] or DEFAULT_GREENHOUSE_BOARDS
    lever_boards = [b for b in configured if b in DEFAULT_LEVER_BOARDS] or DEFAULT_LEVER_BOARDS

    tasks = [fetch_greenhouse_jobs(b) for b in gh_boards] + [fetch_lever_jobs(b) for b in lever_boards]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, list):
            all_jobs.extend(res)
    return all_jobs


def sync_jobs_to_db(db: Session, fetched_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    added_count = 0
    updated_count = 0
    active_source_ids = set()

    # 1. Deactivate demo sources completely (e.g. leverdemo)
    demo_sources_removed = 0
    try:
        demo_jobs = db.query(Job).filter(
            or_(
                Job.source == "leverdemo",
                Job.company.ilike("%leverdemo%"),
                Job.source_job_id.ilike("%leverdemo%"),
            )
        ).all()
        for dj in demo_jobs:
            dj.is_active = False
            dj.last_checked_at = now
            demo_sources_removed += 1
        if demo_sources_removed:
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating demo jobs: {e}")

    # 2. Pre-fetch existing external jobs in bulk for fast O(1) dictionary lookups
    synced_sources = {"greenhouse", "lever"}
    existing_jobs = db.query(Job).filter(Job.source.in_(synced_sources)).all()
    existing_map = {(j.source, j.source_job_id): j for j in existing_jobs}

    new_objects = []

    for job_data in fetched_jobs:
        source = job_data["source"]
        source_job_id = job_data["source_job_id"]
        key = (source, source_job_id)
        active_source_ids.add(key)

        existing = existing_map.get(key)
        if existing:
            existing.title = job_data["title"][:95]
            existing.company = job_data["company"][:95]
            existing.location = job_data["location"][:95]
            existing.job_type = job_data["job_type"][:45]
            existing.description = job_data["description"]
            existing.requirements = job_data["requirements"]
            existing.skills = job_data["skills"]
            existing.required_skills = job_data["skills"]
            existing.application_url = job_data["application_url"][:490]
            existing.is_remote = job_data["is_remote"]
            existing.is_active = True
            existing.last_checked_at = now
            updated_count += 1
        else:
            new_job = Job(
                source=source,
                source_job_id=source_job_id,
                company=job_data["company"][:95],
                title=job_data["title"][:95],
                location=job_data["location"][:95],
                job_type=job_data["job_type"][:45],
                description=job_data["description"],
                requirements=job_data["requirements"],
                skills=job_data["skills"],
                required_skills=job_data["skills"],
                application_url=job_data["application_url"][:490],
                is_remote=job_data["is_remote"],
                posted_at=job_data["posted_at"],
                last_checked_at=now,
                is_active=True,
            )
            new_objects.append(new_job)
            existing_map[key] = new_job
            added_count += 1

    try:
        db.commit()  # commit all updates first
        if new_objects:
            chunk_size = 100
            for i in range(0, len(new_objects), chunk_size):
                db.add_all(new_objects[i : i + chunk_size])
                db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Batch insert error: {e}")

    # 3. Mark jobs no longer returned by external ATS as inactive
    deactivated_count = 0
    try:
        external_jobs = db.query(Job).filter(Job.source.in_(synced_sources), Job.is_active == True).all()
        for ej in external_jobs:
            if (ej.source, ej.source_job_id) not in active_source_ids:
                ej.is_active = False
                ej.last_checked_at = now
                deactivated_count += 1
        if deactivated_count:
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking inactive jobs: {e}")

    # Invalidate job caches
    cache_service.delete_pattern("jobs:*")
    cache_service.delete_pattern("companies:*")
    cache_service.delete_pattern("dashboard:*")

    # Calculate India & Entry Level counts
    india_jobs_count = 0
    entry_level_count = 0
    try:
        india_conditions = [Job.location.ilike(f"%{kw}%") for kw in INDIA_LOCATION_KEYWORDS]
        india_jobs_count = db.query(Job).filter(Job.is_active == True, or_(*india_conditions)).count()

        entry_terms = ["intern", "graduate", "associate", "fresher", "junior", "entry", "trainee", "software", "developer", "analyst", "qa", "devops", "cloud", "ai"]
        entry_conditions = [Job.title.ilike(f"%{t}%") for t in entry_terms]
        entry_level_count = db.query(Job).filter(Job.is_active == True, or_(*entry_conditions)).count()
    except Exception as e:
        logger.error(f"Error computing metric counts: {e}")

    configured_boards = DEFAULT_GREENHOUSE_BOARDS + DEFAULT_LEVER_BOARDS

    summary = {
        "total_fetched": len(fetched_jobs),
        "added": added_count,
        "updated": updated_count,
        "deactivated": deactivated_count,
        "demo_sources_removed": demo_sources_removed,
        "total_active_synced": db.query(Job).filter(Job.is_active == True).count(),
        "india_jobs_count": india_jobs_count,
        "entry_level_count": entry_level_count,
        "companies_configured": len(configured_boards),
        "configured_company_list": configured_boards,
    }
    logger.info(f"Job Sync Completed: {summary}")
    return summary


def run_job_sync_pipeline() -> Dict[str, Any]:
    try:
        fetched_jobs = asyncio.run(fetch_all_external_jobs())
        db = SessionLocal()
        try:
            return sync_jobs_to_db(db, fetched_jobs)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to execute job sync pipeline: {e}")
        return {"total_fetched": 0, "added": 0, "updated": 0, "deactivated": 0, "error": str(e)}
