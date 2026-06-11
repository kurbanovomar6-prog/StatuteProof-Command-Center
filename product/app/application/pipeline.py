"""
RegRadar scraping pipeline — production-ready.

Flow per regulator:
  1. load config (DB, no hardcoded values)
  2. discover new document URLs (strategy-aware)
  3. url-level prefilter (no download needed)
  4. download via proxy_pool (geo-aware, only for restricted domains)
  5. extract text with OCR fallback chain
  6. text-level prefilter (saves GPT tokens)
  7. AI extraction (structured regulation metadata)
  8. save + deep AI analysis (legal/risk/action plan)
  9. emit metrics
"""
import hashlib
import json
import logging
import time
from datetime import datetime

import httpx

from app.infrastructure.scrapers.static import StaticScraper
from app.infrastructure.scrapers.text_extractor import extract_text_from_pdf
from app.infrastructure.scrapers.prefilter import is_regulatory, is_regulatory_url
from app.infrastructure.scrapers.discovery import find_document_urls, get_known_hashes_from_db
from app.infrastructure.scrapers.proxy_pool import proxy_pool
from app.infrastructure.scrapers.fetch_utils import fetch_bytes, pdf_content_hash
from app.infrastructure.scrapers.text_extractor import MANUAL_REVIEW_FLAG
from app.infrastructure.scrapers.metrics import RunMetrics, save_metrics, get_link_discovery_delta
from app.infrastructure.scrapers.regulator_config import RegulatorConfig, load_all
from app.infrastructure.ai.extractor import extract_regulation
from app.infrastructure.ai.analyzer import run_multi_agent
from app.infrastructure.db.repository import RegulationRepository
from app.infrastructure.db.session import engine
from app.core.domain.enums import Jurisdiction
from sqlalchemy import text as _sql

log = logging.getLogger(__name__)
_repo = RegulationRepository()
_scraper = StaticScraper()


def _save_ai_analysis(source_url: str, analysis: dict) -> None:
    h = hashlib.sha256(source_url.encode()).hexdigest()
    with engine.connect() as c:
        c.execute(
            _sql("UPDATE regulations SET ai_analysis=:ai WHERE url_hash=:h"),
            {"ai": json.dumps(analysis, ensure_ascii=False), "h": h},
        )
        c.commit()


def _fetch_pdf(url: str, proxy_required: bool) -> bytes:
    """Download PDF via proxy_pool (geo-aware) or direct."""
    if proxy_required:
        resp = proxy_pool.get(url, timeout=30)
    else:
        resp = httpx.get(
            url, timeout=30, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
        )
    resp.raise_for_status()
    return resp.content


def process_regulator(cfg: RegulatorConfig) -> RunMetrics:
    """Process a single regulator. Returns RunMetrics for observability."""
    m = RunMetrics(regulator=cfg.name, jurisdiction=cfg.jurisdiction)
    t_start = time.monotonic()

    log.info("[%s] ▶  %s  strategy=%s", cfg.jurisdiction, cfg.name, cfg.strategy)

    # ── 1. Discover new document URLs ─────────────────────────────
    known_hashes = get_known_hashes_from_db()
    # Загружаем content-хэши для дедупликации по содержимому PDF
    with engine.connect() as _c:
        _rows = _c.execute(_sql(
            "SELECT content_hash FROM regulations WHERE content_hash IS NOT NULL"
        )).fetchall()
    known_content_hashes: set[str] = {r[0] for r in _rows}
    try:
        jur = Jurisdiction(cfg.jurisdiction)
    except ValueError:
        log.warning("Unknown jurisdiction %s, skipping", cfg.jurisdiction)
        return m

    try:
        urls = find_document_urls(
            base_url=cfg.base_url,
            link_pattern=cfg.link_pattern,
            strategy=cfg.strategy,
            known_hashes=known_hashes,
            article_pattern=cfg.article_pattern,
        )
    except Exception as e:
        log.warning("[WARN] %s discovery failed: %s", cfg.name, str(e)[:120])
        urls = []

    m.links_found = len(urls) + len(known_hashes)  # approximate total on page
    m.links_new   = len(urls)

    # Metric 3: structural change detection
    delta = get_link_discovery_delta(cfg.name, len(urls))
    if delta < 0.1 and len(urls) == 0:
        log.error("[ALERT] %s: links_delta=%.2f — possible block or layout change",
                  cfg.name, delta)
    elif delta > 3.0:
        log.warning("[ALERT] %s: links_delta=%.2f — scraping unexpected content",
                    cfg.name, delta)

    if not urls:
        m.duration_sec = time.monotonic() - t_start
        m.log_summary()
        save_metrics(m)
        return m

    # ── 2. Process each URL ────────────────────────────────────────
    max_docs = cfg.max_docs

    for url in urls[:max_docs]:

        # URL-level prefilter (no download)
        url_ok, url_reason = is_regulatory_url(url)
        if not url_ok:
            log.debug("[PRE-URL] skip — %s | %s", url_reason, url[-50:])
            m.prefilter_url_skip += 1
            continue

        try:
            # Download (proxy-aware)
            pdf_bytes = _fetch_pdf(url, cfg.proxy_required)
            m.docs_downloaded += 1

            # Content-hash дедупликация: пропускаем если PDF уже обработан
            c_hash = pdf_content_hash(pdf_bytes)
            if c_hash in known_content_hashes:
                log.debug("[DEDUP] пропуск по content-hash %s | %s", c_hash[:12], url[-50:])
                continue
            known_content_hashes.add(c_hash)

            # Extract text with OCR fallback
            doc_text = extract_text_from_pdf(pdf_bytes)

            # Документ требует ручной проверки (зашифрован/битый)
            if doc_text == MANUAL_REVIEW_FLAG:
                log.warning("[MANUAL_REVIEW] %s", url[-60:])
                _repo.upsert_raw({
                    "title":        f"[Требует проверки] {url.split('/')[-1]}",
                    "jurisdiction": cfg.jurisdiction,
                    "source_url":   url,
                    "status":       "HUMAN_REVIEW",
                    "source_type":  "WEB",
                    "confidence":   0.0,
                    "critical_level": "LOW",
                    "summary":      "Документ не поддаётся автоматической обработке. Требуется ручной OCR.",
                })
                m.errors += 1
                continue

            if len(doc_text) >= 150:
                m.docs_with_text += 1
            else:
                log.warning("extractor yielded %d chars from %s", len(doc_text), url[-50:])
                continue

            # Text-level prefilter
            text_ok, text_reason = is_regulatory(
                doc_text, cfg.jurisdiction,
                extra_keywords=cfg.prefilter_keywords,
            )
            if not text_ok:
                log.info("[PRE-TEXT] skip — %s | %s", text_reason, url[-50:])
                m.prefilter_text_skip += 1
                continue

            m.prefilter_passed += 1
            m.ai_tokens_est += len(doc_text[:4000]) // 4

            # AI extraction
            reg = extract_regulation(doc_text, jur, source_url=url)
            if _repo.upsert(reg):
                m.saved += 1
                # Deep AI analysis + Action Plan + Urgency Score
                analysis: dict = {}
                try:
                    analysis = run_multi_agent(doc_text, cfg.jurisdiction)
                    _save_ai_analysis(url, analysis)
                    m.ai_success += 1
                    log.info("[AI] ✓ %s", url[-60:])
                except Exception as ai_err:
                    m.ai_fail += 1
                    log.warning("[AI] ✗ %s — %s", url[-50:], ai_err)

                # Генерация структурированного плана действий
                try:
                    from app.application.action_plan import (
                        generate_compliance_action_plan, save_action_plan,
                    )
                    critical_level = (
                        getattr(reg, "critical_level", "LOW")
                        if hasattr(reg, "critical_level")
                        else str(reg.get("critical_level", "LOW"))
                    )
                    if critical_level in ("CRITICAL", "HIGH") and analysis:
                        plan = generate_compliance_action_plan(
                            ai_analysis=analysis,
                            regulation_title=getattr(reg, "title", "") or "",
                            jurisdiction=cfg.jurisdiction,
                            critical_level=critical_level,
                            effective_date=str(getattr(reg, "effective_date", "") or ""),
                        )
                        save_action_plan(url, plan, plan["urgency_score"])
                        log.info(
                            "[ACTION_PLAN] ✓ urgency=%d/10 %s",
                            plan["urgency_score"], url[-50:],
                        )
                except Exception as plan_err:
                    log.debug("[ACTION_PLAN] ✗ %s — %s", url[-50:], plan_err)

                # Сохраняем compute_cost_usd и time_to_discovery_sec
                try:
                    import hashlib as _hl
                    from datetime import timedelta as _td
                    from app.infrastructure.db.session import engine as _eng
                    from app.infrastructure.analytics.ytd_metrics import (
                        compute_time_to_discovery, _LLM_COST_PER_DOC,
                    )
                    url_hash = _hl.sha256(url.encode()).hexdigest()
                    pub_date = str(getattr(reg, "publication_date", "") or "")
                    disc_sec = compute_time_to_discovery(pub_date or None, datetime.utcnow())
                    with _eng.connect() as _c:
                        _c.execute(
                            _sql("UPDATE regulations SET compute_cost_usd=:cost, "
                                 "time_to_discovery_sec=:disc WHERE url_hash=:h"),
                            {"cost": _LLM_COST_PER_DOC, "disc": disc_sec, "h": url_hash},
                        )
                        _c.commit()
                except Exception:
                    pass

                # Push-уведомления при CRITICAL/HIGH — Telegram + Webhook (БД) + env Webhook
                try:
                    reg_dict = {
                        "id":             getattr(reg, "id", None),
                        "title":          getattr(reg, "title", ""),
                        "jurisdiction":   cfg.jurisdiction,
                        "critical_level": (
                            getattr(reg, "critical_level", "LOW")
                            if hasattr(reg, "critical_level")
                            else str(reg.get("critical_level", "LOW"))
                        ),
                        "effective_date": str(getattr(reg, "effective_date", "") or ""),
                        "summary":        getattr(reg, "summary", "") or "",
                        "source_url":     url,
                        "urgency_score":  analysis.get("urgency_score"),
                        "action_plan":    analysis.get("action"),
                        "fines":          analysis.get("fines"),
                    }
                    from app.infrastructure.notifications.telegram_alert import notify_regulation as _tg_notify
                    from app.infrastructure.notifications.webhook import notify_regulation as _wh_notify
                    from app.api.v1.webhooks_controller import notify_regulation_via_db as _wh_db_notify
                    _tg_notify(reg_dict)
                    _wh_notify(reg_dict)        # env-based webhook (legacy)
                    _wh_db_notify(reg_dict)     # DB-based webhook endpoints (new)
                except Exception as notify_err:
                    log.debug("[NOTIFY] ошибка отправки уведомления — %s", notify_err)

        except Exception as e:
            m.errors += 1
            log.error("[ERR] %s — %s", url[-50:], e)

    # ── 3. Emit metrics ────────────────────────────────────────────
    m.duration_sec = time.monotonic() - t_start
    m.log_summary()
    save_metrics(m)

    return m


def process_telegram_channels(channels: dict[str, str] | None = None) -> int:
    from app.infrastructure.scrapers.telegram_monitor import run_all_channels

    if channels is None:
        # Pull tg_channel from regulator configs
        channels = {
            cfg.jurisdiction: cfg.tg_channel
            for cfg in load_all()
            if cfg.tg_channel
        }

    with engine.connect() as c:
        rows = c.execute(
            _sql("SELECT source_url FROM regulations WHERE source_type='TELEGRAM_INTEL'")
        ).fetchall()
    known_urls = {r[0] for r in rows}

    records = run_all_channels(channels=channels or None, known_urls=known_urls)
    saved = 0

    for rec in records:
        raw_text = rec.pop("text", "")
        try:
            if _repo.upsert_raw(rec):
                saved += 1
                try:
                    analysis = run_multi_agent(raw_text, rec["jurisdiction"])
                    _save_ai_analysis(rec["source_url"], analysis)
                except Exception as ai_err:
                    log.warning("[TG-AI] ✗ %s", ai_err)
        except Exception as e:
            log.error("TG record error: %s", e)

    log.info("Telegram: %d new records saved", saved)
    return saved


def run_all_regulators() -> int:
    """Main entry point. Returns total documents saved."""
    total = 0
    for cfg in load_all():
        m = process_regulator(cfg)
        total += m.saved
    return total
