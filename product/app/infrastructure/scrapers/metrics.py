"""
Pipeline observability — 3 critical metrics for scraper health monitoring.

Metric 1: extraction_yield_ratio
  docs_with_text / docs_downloaded
  Drops to 0 → site changed structure, returns HTML instead of PDF, or IP blocked.

Metric 2: prefilter_pass_rate
  docs_passed_prefilter / docs_downloaded
  Spikes to 100% → prefilter too permissive (keywords too generic).
  Drops to 0%   → prefilter over-filtering OR site returning garbage.

Metric 3: link_discovery_count_delta
  current_run_links_found vs. rolling_avg_over_last_7_runs
  Delta > 3x   → site layout changed, collecting non-document links.
  Delta < 0.1x → site blocked us or moved content.

All metrics are written to DB (scrape_metrics table) and logged.
No external service required — SQLite is enough for a single-node setup.
"""
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime

from sqlalchemy import text

log = logging.getLogger(__name__)


@dataclass
class RunMetrics:
    regulator: str
    jurisdiction: str
    run_at: str = ""

    # Discovery
    links_found: int = 0
    links_new: int = 0

    # Download
    docs_downloaded: int = 0
    docs_with_text: int = 0       # Metric 1 numerator
    docs_ocr_used: int = 0

    # Prefilter
    prefilter_url_skip: int = 0
    prefilter_text_skip: int = 0
    prefilter_passed: int = 0     # Metric 2 numerator

    # AI
    ai_success: int = 0
    ai_fail: int = 0
    ai_tokens_est: int = 0        # rough: chars_sent / 4

    # Outcome
    saved: int = 0
    errors: int = 0
    duration_sec: float = 0.0

    def extraction_yield(self) -> float:
        """Metric 1: fraction of downloaded docs that had extractable text."""
        return (self.docs_with_text / self.docs_downloaded
                if self.docs_downloaded else 0.0)

    def prefilter_pass_rate(self) -> float:
        """Metric 2: fraction of downloaded docs that passed prefilter."""
        return (self.prefilter_passed / self.docs_downloaded
                if self.docs_downloaded else 0.0)

    def log_summary(self):
        yield_pct   = round(self.extraction_yield() * 100)
        pass_pct    = round(self.prefilter_pass_rate() * 100)

        # Metric 3: alert if links_found is 0 but regulator should have documents
        link_alert = " ⚠ ZERO LINKS" if self.links_found == 0 else ""

        log.info(
            "[METRICS] %s | links=%d%s | yield=%d%% | prefilter_pass=%d%% | "
            "saved=%d | ai_ok=%d | tokens_est≈%d | dur=%.1fs",
            self.regulator[:25], self.links_found, link_alert,
            yield_pct, pass_pct,
            self.saved, self.ai_success, self.ai_tokens_est, self.duration_sec,
        )

        # Alert thresholds
        if self.docs_downloaded > 0 and yield_pct < 20:
            log.error(
                "[ALERT] %s: extraction_yield=%d%% — possible IP block, "
                "HTML-as-PDF, or broken extractor", self.regulator, yield_pct,
            )
        if self.docs_downloaded > 3 and pass_pct == 0:
            log.error(
                "[ALERT] %s: prefilter_pass_rate=0%% — all docs rejected, "
                "check keywords or site content change", self.regulator,
            )


def save_metrics(metrics: RunMetrics) -> None:
    """Persist metrics to scrape_metrics table for trend analysis."""
    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as c:
            c.execute(text("""
                CREATE TABLE IF NOT EXISTS scrape_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regulator TEXT,
                    jurisdiction TEXT,
                    run_at TEXT,
                    payload TEXT,
                    extraction_yield REAL,
                    prefilter_pass_rate REAL,
                    links_found INTEGER,
                    saved INTEGER
                )"""))
            c.execute(text("""
                INSERT INTO scrape_metrics
                (regulator, jurisdiction, run_at, payload, extraction_yield,
                 prefilter_pass_rate, links_found, saved)
                VALUES (:reg, :jur, :run_at, :payload, :ey, :ppr, :lf, :saved)
            """), {
                "reg":     metrics.regulator,
                "jur":     metrics.jurisdiction,
                "run_at":  datetime.utcnow().isoformat(),
                "payload": json.dumps(asdict(metrics)),
                "ey":      metrics.extraction_yield(),
                "ppr":     metrics.prefilter_pass_rate(),
                "lf":      metrics.links_found,
                "saved":   metrics.saved,
            })
            c.commit()
    except Exception as e:
        log.warning("save_metrics failed: %s", e)


def get_link_discovery_delta(regulator: str, current: int) -> float:
    """
    Metric 3: compare current links_found to rolling average of last 7 runs.
    Returns ratio: 1.0 = normal, <0.1 = blocked, >3.0 = scraping garbage.
    """
    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT links_found FROM scrape_metrics "
                "WHERE regulator=:r ORDER BY id DESC LIMIT 7"
            ), {"r": regulator}).fetchall()
        if not rows:
            return 1.0  # no history yet
        avg = sum(r[0] for r in rows) / len(rows)
        if avg == 0:
            return 1.0
        return current / avg
    except Exception:
        return 1.0
