"""
Isolated background scraping workers.
Run as a separate process: python scheduler_workers.py
NiceGUI never calls scrapers directly — it only reads the DB and calls trigger_scrape().
"""
import sys
import hashlib
import io
from datetime import datetime
from pathlib import Path

from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from config import settings
from database import (
    init_db, reg_repo, reg_repo_r, job_repo, DEFAULT_REGULATORS
)

# ── Sentry (optional, no-op if DSN empty) ────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
    logger.info("Sentry activated")

# ── Loguru setup ─────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
    level=settings.LOG_LEVEL,
    colorize=True,
)
logger.add(
    settings.LOG_DIR / "workers_{time:YYYY-MM-DD}.log",
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    level="DEBUG",
    encoding="utf-8",
)


# ── Core scraping logic ───────────────────────────────────────────
def _fetch_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts).strip()
    except Exception as e:
        logger.debug("pdfplumber error: {}", e)
        return ""


def _extract_with_ai(text: str, jurisdiction: str, url: str) -> dict | None:
    try:
        import instructor
        from anthropic import Anthropic
        from app.core.domain.models import RegulationModel
        from app.core.domain.enums import Jurisdiction

        client = instructor.from_anthropic(Anthropic())
        reg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            max_retries=2,
            system="Extract regulation metadata for CIS countries. Be precise with dates (YYYY-MM-DD).",
            messages=[{"role": "user", "content": f"Jurisdiction: {jurisdiction}\n\nText:\n{text[:3000]}\n\nSource: {url}"}],
            response_model=RegulationModel,
        )
        return {
            "title": reg.title,
            "jurisdiction": reg.jurisdiction.value,
            "publication_date": str(reg.publication_date),
            "effective_date": str(reg.effective_date),
            "summary": reg.summary,
            "industries": ",".join(reg.industries),
            "critical_level": reg.critical_level.value,
            "source_url": url,
            "confidence": reg.confidence,
            "status": reg.status.value,
            "extracted_at": datetime.utcnow(),
        }
    except Exception as e:
        logger.warning("AI extraction failed for {}: {}", url, e)
        if settings.SENTRY_DSN:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        return None


def scrape_regulator(name: str, base_url: str, jurisdiction: str, link_pattern: str = ".pdf"):
    """Single regulator scraping job — runs in thread pool."""
    job_id = job_repo.create(name, jurisdiction)
    logger.info("Job #{} started: {} ({})", job_id, name, jurisdiction)

    import httpx
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    docs_found = docs_saved = 0
    error_msg = None

    try:
        with httpx.Client(headers=headers, timeout=settings.SCRAPE_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.get(base_url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [
                urljoin(base_url, a["href"])
                for a in soup.find_all("a", href=True)
                if link_pattern.lower() in a["href"].lower()
            ]
            logger.debug("Found {} PDF links at {}", len(links), base_url)
            docs_found = len(links)

            for url in links[:8]:
                try:
                    pdf_resp = client.get(url)
                    pdf_resp.raise_for_status()
                    text = _fetch_text_from_pdf(pdf_resp.content)
                    if len(text) < 80:
                        continue
                    data = _extract_with_ai(text, jurisdiction, url)
                    if data and reg_repo.upsert(data):
                        docs_saved += 1
                        logger.info("Saved: {}", data["title"][:70])
                except Exception as e:
                    logger.warning("PDF error {}: {}", url, e)

    except Exception as e:
        error_msg = str(e)
        logger.error("Regulator {} failed: {}", name, e)
        if settings.SENTRY_DSN:
            import sentry_sdk
            sentry_sdk.capture_exception(e)

    job_repo.finish(job_id, docs_found, docs_saved, error_msg)
    logger.success("Job #{} done — found:{} saved:{}", job_id, docs_found, docs_saved)


def run_all_regulators():
    """Trigger a scrape job for every active regulator."""
    regulators = reg_repo_r.all_active()
    if not regulators:
        logger.warning("No active regulators configured")
        return
    logger.info("Launching {} regulator jobs", len(regulators))
    for r in regulators:
        try:
            scrape_regulator(r.name, r.base_url, r.jurisdiction, r.link_pattern)
        except Exception as e:
            logger.error("Unhandled error for {}: {}", r.name, e)


# ── APScheduler factory ───────────────────────────────────────────
def build_scheduler() -> BackgroundScheduler:
    executors = {"default": ThreadPoolExecutor(max_workers=settings.SCRAPE_MAX_WORKERS)}
    scheduler = BackgroundScheduler(executors=executors, timezone="UTC")
    scheduler.add_job(
        run_all_regulators,
        trigger="interval",
        hours=settings.SCRAPE_INTERVAL_HOURS,
        id="full_scrape",
        replace_existing=True,
        misfire_grace_time=300,
    )
    return scheduler


# ── Standalone entry point ────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    reg_repo_r.seed(DEFAULT_REGULATORS)

    scheduler = build_scheduler()
    scheduler.start()
    logger.success(
        "Scheduler started — scraping every {}h. Press Ctrl+C to stop.",
        settings.SCRAPE_INTERVAL_HOURS,
    )
    # Fire immediately on first run
    scheduler.get_job("full_scrape").modify(next_run_time=datetime.utcnow())

    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
