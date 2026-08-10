import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.job import Job
from app.services.nlp_utils import detect_skills
from app.services.cache_service import cache_service

logger = logging.getLogger("careerpilot.job_sync")

# Supported official company boards for Greenhouse and Lever
DEFAULT_GREENHOUSE_BOARDS = ["cloudflare", "gitlab", "stripe", "figma", "hashicorp"]
DEFAULT_LEVER_BOARDS = ["leverdemo", "elastic"]


def _clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    # Strip HTML tags for clean text descriptions
    clean = re.sub(r"<[^>]+>", " ", html_text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:5000]


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
                job_id = str(item.get("id"))
                title = item.get("title", "").strip()
                location = (item.get("location", {}) or {}).get("name", "Remote").strip()
                html_content = item.get("content", "")
                clean_desc = _clean_html(html_content)
                app_url = item.get("absolute_url", "")
                
                is_remote = "remote" in location.lower() or "remote" in title.lower() or "work from home" in clean_desc.lower()
                job_type = _determine_job_type(title, clean_desc)
                skills = detect_skills(title + " " + clean_desc)

                parsed_jobs.append({
                    "source": "greenhouse",
                    "source_job_id": job_id[:95],
                    "company": board.capitalize()[:140],
                    "title": title[:140],
                    "location": (location if location else "Remote")[:140],
                    "job_type": job_type[:45],
                    "description": clean_desc if clean_desc else title,
                    "requirements": "See official application page for full requirements.",
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
                job_id = str(item.get("id"))
                title = item.get("text", "").strip()
                cats = item.get("categories", {}) or {}
                location = cats.get("location", "Remote") or "Remote"
                commitment = cats.get("commitment", "Full-Time") or "Full-Time"
                desc_html = item.get("descriptionHtml", "") or ""
                clean_desc = _clean_html(desc_html)
                app_url = item.get("hostedUrl", "") or item.get("applyUrl", "")
                
                is_remote = "remote" in location.lower() or "remote" in title.lower() or "work from home" in clean_desc.lower()
                job_type = _determine_job_type(title + " " + commitment, clean_desc)
                skills = detect_skills(title + " " + clean_desc)

                parsed_jobs.append({
                    "source": "lever",
                    "source_job_id": job_id[:95],
                    "company": company.capitalize()[:140],
                    "title": title[:140],
                    "location": (location if location else "Remote")[:140],
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
    
    # Custom configured boards or defaults
    configured_boards = [b.strip().lower() for b in settings.DEFAULT_JOB_BOARDS.split(",") if b.strip()]
    gh_boards = [b for b in configured_boards if b in DEFAULT_GREENHOUSE_BOARDS] or DEFAULT_GREENHOUSE_BOARDS
    lever_boards = [b for b in configured_boards if b in DEFAULT_LEVER_BOARDS] or DEFAULT_LEVER_BOARDS

    tasks = [fetch_greenhouse_jobs(b) for b in gh_boards] + [fetch_lever_jobs(b) for b in lever_boards]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, list):
            all_jobs.extend(res)
    return all_jobs


def sync_jobs_to_db(db: Session, fetched_jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    now = datetime.now(timezone.utc)
    added_count = 0
    updated_count = 0
    active_source_ids = set()

    for job_data in fetched_jobs:
        source = job_data["source"]
        source_job_id = job_data["source_job_id"]
        key = (source, source_job_id)
        active_source_ids.add(key)

        try:
            existing = db.query(Job).filter(Job.source == source, Job.source_job_id == source_job_id).first()

            if existing:
                existing.title = job_data["title"][:140]
                existing.company = job_data["company"][:140]
                existing.location = job_data["location"][:140]
                existing.job_type = job_data["job_type"][:45]
                existing.description = job_data["description"]
                existing.requirements = job_data["requirements"]
                existing.skills = job_data["skills"]
                existing.required_skills = job_data["skills"]
                existing.application_url = job_data["application_url"][:490]
                existing.is_remote = job_data["is_remote"]
                existing.is_active = True
                existing.last_checked_at = now
                db.commit()
                updated_count += 1
            else:
                new_job = Job(
                    source=source,
                    source_job_id=source_job_id,
                    company=job_data["company"][:140],
                    title=job_data["title"][:140],
                    location=job_data["location"][:140],
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
                db.add(new_job)
                db.commit()
                added_count += 1
        except Exception as e:
            db.rollback()
            logger.warning(f"Error saving job '{job_data.get('title')}' ({source}/{source_job_id}): {e}")

    # Mark jobs no longer returned by external ATS as inactive (without deleting user applications)
    deactivated_count = 0
    try:
        synced_sources = {"greenhouse", "lever"}
        external_jobs = db.query(Job).filter(Job.source.in_(synced_sources), Job.is_active == True).all()

        for ej in external_jobs:
            if (ej.source, ej.source_job_id) not in active_source_ids:
                ej.is_active = False
                ej.last_checked_at = now
                deactivated_count += 1
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking inactive jobs: {e}")

    # Invalidate job caches
    cache_service.delete_pattern("jobs:*")
    cache_service.delete_pattern("companies:*")
    cache_service.delete_pattern("dashboard:*")

    summary = {
        "total_fetched": len(fetched_jobs),
        "added": added_count,
        "updated": updated_count,
        "deactivated": deactivated_count,
    }
    logger.info(f"Job Sync Completed: {summary}")
    return summary



def run_job_sync_pipeline() -> Dict[str, int]:
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
