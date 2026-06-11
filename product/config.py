"""Centralized configuration for RegRadar."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Railway (и большинство PaaS) инжектит PORT, а не APP_PORT.
# Прокидываем его до загрузки .env чтобы Pydantic Settings подхватил.
if "PORT" in os.environ and "APP_PORT" not in os.environ:
    os.environ["APP_PORT"] = os.environ["PORT"]

# Load from the global .env (Anthropic key lives there)
# Path(__file__) = .../регrada/config.py → 3 parents = .../obsidian
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)
load_dotenv(Path(__file__).parent / ".env", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── API Keys ──────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    SENTRY_DSN: str = ""
    NGROK_AUTHTOKEN: str = ""  # from https://dashboard.ngrok.com

    # ── App ───────────────────────────────────────────────────────
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    DEBUG: bool = False
    APP_TITLE: str = "RegRadar"
    ENABLE_TUNNEL: bool = False  # set True to auto-expose via pyngrok

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./regrada.db"

    # ── Scheduler ────────────────────────────────────────────────
    SCRAPE_INTERVAL_HOURS: int = 6
    SCRAPE_MAX_WORKERS: int = 4
    SCRAPE_TIMEOUT_SECONDS: int = 60

    # ── Camoufox / Browser Fingerprint ───────────────────────────
    CAMOUFOX_OS: str = "windows"            # "windows" | "macos" | "linux"
    CAMOUFOX_HEADLESS: bool = True
    CAMOUFOX_SCREEN_W: int = 1920
    CAMOUFOX_SCREEN_H: int = 1080

    # ── Proxy pool for CIS portals (comma-separated) ──────────────
    # Format: "http://user:pass@host:port,http://..."
    PROXY_LIST: str = ""

    # ── API security ─────────────────────────────────────────────
    REGRADA_API_KEY: str = ""   # set to protect /api/* endpoints
    SECRET_KEY: str = "regrada-dev-secret-change-in-prod"  # NiceGUI storage_secret

    # ── Pre-filter thresholds ────────────────────────────────────
    PREFILTER_MIN_CHARS: int = 400
    PREFILTER_MAX_CHARS: int = 120_000

    # ── Scraper defaults ──────────────────────────────────────────
    SCRAPER_MAX_DOCS_DEFAULT: int = 15
    SCRAPER_REQUEST_TIMEOUT: int = 30
    OCR_MIN_CHARS: int = 150

    # ── Proxy pool health ─────────────────────────────────────────
    PROXY_FAILURE_THRESHOLD: int = 3
    PROXY_COOLDOWN_SEC: int = 30

    # ── Observability thresholds ──────────────────────────────────
    METRICS_YIELD_ALERT_PCT: int = 20
    METRICS_LINK_DELTA_LOW: float = 0.1
    METRICS_LINK_DELTA_HIGH: float = 3.0

    # ── UI / display ─────────────────────────────────────────────
    URGENCY_YELLOW_DAYS: int = 14
    PAGINATION_DEFAULT: int = 25

    # ── Logging ──────────────────────────────────────────────────
    LOG_DIR: Path = Path("logs")
    LOG_ROTATION: str = "50 MB"
    LOG_RETENTION: str = "30 days"
    LOG_LEVEL: str = "INFO"

    @property
    def proxy_list(self) -> list[str]:
        return [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]

    @property
    def camoufox_profile(self) -> dict:
        return {
            "os": self.CAMOUFOX_OS,
            "screen": {"max_width": self.CAMOUFOX_SCREEN_W, "max_height": self.CAMOUFOX_SCREEN_H},
        }


settings = Settings()
settings.LOG_DIR.mkdir(exist_ok=True)

# ── Jurisdictions metadata ────────────────────────────────────────
JURISDICTIONS = {
    "RU": {"label": "Россия",      "flag": "🇷🇺"},
    "KZ": {"label": "Казахстан",   "flag": "🇰🇿"},
    "AZ": {"label": "Азербайджан", "flag": "🇦🇿"},
    "BY": {"label": "Беларусь",    "flag": "🇧🇾"},
    "UZ": {"label": "Узбекистан",  "flag": "🇺🇿"},
}

RISK_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "MEDIUM":   "#d97706",
    "LOW":      "#059669",
}
