"""
RegRadar — entry point.
Page logic lives in src/pages/. This file wires routers, logging, and startup.
"""
import sys
import threading

from fastapi.responses import JSONResponse
from loguru import logger
from nicegui import ui, app

from config import settings
from database import init_db, reg_repo_r, DEFAULT_REGULATORS
from src.styles import GLOBAL_CSS
from src.pages.dashboard import router as dashboard_router
from src.pages.tasks import router as tasks_router
from src.pages.settings import router as settings_router

# ── Health endpoints ──────────────────────────────────────────────
async def _health_check() -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "regrada"})

app.add_api_route("/health",        _health_check, methods=["GET"], include_in_schema=False)
app.add_api_route("/api/v1/health", _health_check, methods=["GET"], include_in_schema=False)

# ── Sentry ───────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

# ── Logging ──────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL, colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
logger.add(settings.LOG_DIR / "ui_{time:YYYY-MM-DD}.log",
           rotation=settings.LOG_ROTATION, retention=settings.LOG_RETENTION, encoding="utf-8")

# ── Global CSS + font ─────────────────────────────────────────────
ui.add_head_html(GLOBAL_CSS, shared=True)
ui.add_head_html(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
    shared=True,
)

# ── Page routers ──────────────────────────────────────────────────
app.include_router(dashboard_router)
app.include_router(tasks_router)
app.include_router(settings_router)


# ══════════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════════

def _start_tunnel() -> None:
    try:
        from pyngrok import ngrok, conf
        if settings.NGROK_AUTHTOKEN:
            conf.get_default().auth_token = settings.NGROK_AUTHTOKEN
        tunnel = ngrok.connect(settings.APP_PORT)
        url = tunnel.public_url
        app.storage.general["tunnel_url"] = url
        logger.success("pyngrok tunnel: {}", url)
        print(f"\n  🌐 Публичный URL: {url}\n")
    except Exception as e:
        logger.warning("pyngrok failed: {}", e)


@app.on_startup
async def on_startup() -> None:
    init_db()
    reg_repo_r.seed(DEFAULT_REGULATORS)
    if settings.ENABLE_TUNNEL:
        threading.Thread(target=_start_tunnel, daemon=True).start()
    logger.success("RegRadar started at http://{}:{}", settings.APP_HOST, settings.APP_PORT)


if __name__ == "__main__":
    ui.run(
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        title=settings.APP_TITLE,
        favicon="📋",
        dark=True,
        reload=False,
        storage_secret=settings.SECRET_KEY,
    )
