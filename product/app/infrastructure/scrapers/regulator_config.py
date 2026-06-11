"""
Centralized regulator configuration loader.

Config is read from DB (regulators table) — single source of truth.
No code changes needed to add/modify regulators.

Each regulator row can carry a JSON `config` column with:
  - article_pattern: regex for FOLLOW_HTML strategy
  - prefilter_keywords: override global keywords for this regulator
  - proxy_required: bool — force proxy even for non-GEO_RESTRICTED domains
  - max_docs: int — per-run document cap (default 15)
  - tg_channel: str — Telegram channel URL for this regulator
  - disabled: bool — skip without deleting

DB schema extension (auto-migrated):
  ALTER TABLE regulators ADD COLUMN config TEXT DEFAULT '{}';
"""
import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache

from sqlalchemy import text

log = logging.getLogger(__name__)


@dataclass
class RegulatorConfig:
    id: int
    name: str
    jurisdiction: str
    base_url: str
    strategy: str = "STATIC"
    link_pattern: str = ".pdf"
    active: bool = True

    # Extended config (from JSON column)
    article_pattern: str = r"\d{4}-\d{2}-\d{2}"
    prefilter_keywords: list[str] = field(default_factory=list)
    proxy_required: bool = False
    max_docs: int = 15
    tg_channel: str = ""
    disabled: bool = False


def _ensure_config_column():
    """Idempotent migration — adds config column if missing."""
    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as c:
            cols = {r[1] for r in c.execute(text("PRAGMA table_info(regulators)"))}
            if "config" not in cols:
                c.execute(text("ALTER TABLE regulators ADD COLUMN config TEXT DEFAULT '{}'"))
                c.commit()
                log.info("regulator_config: added config column to regulators table")
    except Exception as e:
        log.warning("_ensure_config_column: %s", e)


def load_all() -> list[RegulatorConfig]:
    """Load all active regulators with their extended config."""
    _ensure_config_column()

    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT id, name, jurisdiction, base_url, strategy, link_pattern, "
                "active, COALESCE(config, '{}') config FROM regulators"
            )).fetchall()
    except Exception as e:
        log.error("load_all regulators failed: %s", e)
        return []

    result: list[RegulatorConfig] = []
    for r in rows:
        try:
            extra = json.loads(r.config or "{}")
        except json.JSONDecodeError:
            extra = {}

        cfg = RegulatorConfig(
            id=r.id,
            name=r.name,
            jurisdiction=r.jurisdiction,
            base_url=r.base_url,
            strategy=(r.strategy or "STATIC").upper(),
            link_pattern=r.link_pattern or ".pdf",
            active=bool(r.active),
            article_pattern=extra.get("article_pattern", r"\d{4}-\d{2}-\d{2}"),
            prefilter_keywords=extra.get("prefilter_keywords", []),
            proxy_required=extra.get("proxy_required", False),
            max_docs=extra.get("max_docs", 15),
            tg_channel=extra.get("tg_channel", ""),
            disabled=extra.get("disabled", False),
        )

        if cfg.active and not cfg.disabled:
            result.append(cfg)

    log.debug("regulator_config: loaded %d active configs", len(result))
    return result


def update_config(regulator_id: int, config_patch: dict) -> bool:
    """
    Merge-update the JSON config for a regulator.
    Use from UI or admin script — no code deploys needed.

    Example:
        update_config(3, {"max_docs": 5, "tg_channel": "https://t.me/s/cbar_az"})
    """
    _ensure_config_column()
    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as c:
            row = c.execute(
                text("SELECT config FROM regulators WHERE id=:i"), {"i": regulator_id}
            ).fetchone()
            if not row:
                return False
            current = json.loads(row[0] or "{}")
            current.update(config_patch)
            c.execute(
                text("UPDATE regulators SET config=:cfg WHERE id=:i"),
                {"cfg": json.dumps(current, ensure_ascii=False), "i": regulator_id},
            )
            c.commit()
        log.info("regulator_config: updated id=%d with %s", regulator_id, config_patch)
        return True
    except Exception as e:
        log.error("update_config failed: %s", e)
        return False
