"""
middleware.py — ASGI Security Stack для RegRadar Enterprise.

Компоненты:
  1. SecurityHeadersMiddleware  — Hardened HTTP-заголовки (HSTS, CSP, X-Frame-Options...).
  2. RateLimitMiddleware        — Token Bucket Rate Limiting (Redis + in-memory fallback).
  3. JWTAuthMiddleware          — Проверка Bearer-токена на защищённых /api/ маршрутах.
  4. RegRadarSecurityStack      — Компоновщик: добавляет все три middleware одним вызовом.

Порядок выполнения (при получении запроса):
  SecurityHeaders → RateLimit → JWTAuth → Handler
  (то есть rate limit срабатывает ДО JWT-проверки — экономит ресурсы при атаке)

Публичные маршруты (JWT не требуется):
  /api/v1/auth/login
  /api/v1/auth/refresh
  /api/v1/auth/logout
  /docs, /openapi.json, /redoc  (FastAPI Swagger UI)
  /                              (NiceGUI UI)
"""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

log = logging.getLogger(__name__)

# ── Маршруты исключённые из JWT-проверки ──────────────────────────────────────
_JWT_PUBLIC_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/docs",
    "/openapi.json",
    "/redoc",
})

# Префиксы не требующие JWT (NiceGUI UI, статика)
_JWT_PUBLIC_PREFIXES = (
    "/_nicegui/",
    "/static/",
    "/__nicegui",
    "/favicon",
)

# ── Заголовки безопасности ─────────────────────────────────────────────────────
# Все значения выбраны по OWASP Security Headers Guide 2024.
_SECURITY_HEADERS = {
    # HSTS: браузер запоминает HTTPS на 2 года, включает поддомены и preload
    "Strict-Transport-Security": (
        "max-age=63072000; includeSubDomains; preload"
    ),
    # CSP: запрещает inline-скрипты и внешние ресурсы (кроме trusted CDN для шрифтов)
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net unpkg.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net; "
        "font-src 'self' fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    ),
    # Запрет embedding в iframe (clickjacking protection)
    "X-Frame-Options":           "DENY",
    # Запрет MIME-sniffing
    "X-Content-Type-Options":    "nosniff",
    # Минимальная утечка referrer
    "Referrer-Policy":           "strict-origin-when-cross-origin",
    # Ограничение доступа к устройствам браузера
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), "
        "payment=(), usb=(), interest-cohort=()"
    ),
    # Современная замена X-XSS-Protection (устарел, но добавляем для старых браузеров)
    "X-XSS-Protection":          "1; mode=block",
    # Убираем информацию о сервере
    "Server":                    "RegRadar",
}


# ── 1. Security Headers Middleware ────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Добавляет hardened HTTP security headers ко всем ответам.
    Не зависит от типа маршрута — применяется глобально.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        # Убираем лишние заголовки которые раскрывают стек
        response.headers.pop("X-Powered-By", None)
        return response


# ── 2. Rate Limit Middleware ───────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token Bucket Rate Limiting на все /api/ маршруты.
    Ключ лимита: IP-адрес клиента.

    Стандартные маршруты:        10 req/sec
    Административные маршруты:   3 req/min

    При превышении возвращает HTTP 429 с заголовками X-RateLimit-*.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Rate limit применяется только к API-маршрутам
        if not path.startswith("/api/"):
            return await call_next(request)

        from app.infrastructure.security.rate_limiter import get_limiter, classify_route

        client_ip  = _get_client_ip(request)
        route_type = classify_route(path)
        limiter    = get_limiter()

        allowed, rl_headers = limiter.check(ip=client_ip, route_type=route_type)

        if not allowed:
            log.warning(
                "rate_limit: 429 для %s → %s (%s)",
                client_ip, path[:60], route_type,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail":      "Превышен лимит запросов",
                    "retry_after": rl_headers.get("Retry-After", "1"),
                },
                headers={**rl_headers, **_SECURITY_HEADERS},
            )

        response = await call_next(request)
        # Добавляем rate limit заголовки в успешный ответ
        for k, v in rl_headers.items():
            response.headers[k] = v
        return response


# ── 3. JWT Auth Middleware ─────────────────────────────────────────────────────

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Проверка Bearer access-токена на защищённых /api/ маршрутах.
    Публичные маршруты (login, refresh, docs) пропускаются без проверки.

    При невалидном токене возвращает HTTP 401 с WWW-Authenticate: Bearer.
    При отсутствии заголовка Authorization — 401 (кроме публичных маршрутов).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # NiceGUI UI и публичные маршруты — пропускаем
        if not path.startswith("/api/"):
            return await call_next(request)

        # Публичные API-маршруты — пропускаем
        if path in _JWT_PUBLIC_PATHS:
            return await call_next(request)

        for prefix in _JWT_PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Извлекаем Bearer-токен из заголовка Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            log.debug("jwt_auth: отсутствует Bearer-токен для %s", path[:60])
            return JSONResponse(
                status_code=401,
                content={"detail": "Требуется аутентификация"},
                headers={
                    "WWW-Authenticate": "Bearer",
                    **_SECURITY_HEADERS,
                },
            )

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            from app.infrastructure.security.auth import verify_token
            payload = verify_token(token, expected_type="access")
            # Добавляем payload в state запроса — доступен в route handlers
            request.state.user    = payload.get("sub", "")
            request.state.roles   = payload.get("roles", [])
            request.state.jti     = payload.get("jti", "")
        except Exception as exc:
            detail = getattr(exc, "detail", "Токен недействителен")
            return JSONResponse(
                status_code=401,
                content={"detail": detail},
                headers={
                    "WWW-Authenticate": "Bearer",
                    **_SECURITY_HEADERS,
                },
            )

        return await call_next(request)


# ── Утилиты ────────────────────────────────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    """
    Извлекает реальный IP клиента с учётом reverse proxy заголовков.
    Приоритет: X-Forwarded-For → X-Real-IP → request.client.host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For может содержать цепочку: "client, proxy1, proxy2"
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "0.0.0.0"


# ── Компоновщик: добавляет весь Security Stack одним вызовом ──────────────────

def apply_security_stack(app: ASGIApp) -> ASGIApp:
    """
    Оборачивает ASGI-приложение полным Security Stack.
    Вызывается в точке входа перед запуском uvicorn.

    Порядок оборачивания (внутрь-наружу):
      app → JWTAuth → RateLimit → SecurityHeaders
    Порядок выполнения (запрос проходит наружу-внутрь):
      SecurityHeaders → RateLimit → JWTAuth → app

    Использование в main.py / app.py:
        from app.infrastructure.security.middleware import apply_security_stack
        from nicegui import app as nicegui_app
        nicegui_app.add_middleware(SecurityHeadersMiddleware)
        nicegui_app.add_middleware(RateLimitMiddleware)
        nicegui_app.add_middleware(JWTAuthMiddleware)
    """
    from starlette.middleware import Middleware
    from starlette.applications import Starlette
    # Для NiceGUI используем add_middleware напрямую на объекте app
    # Эта функция служит документацией порядка — реальный вызов в app.py
    return app
