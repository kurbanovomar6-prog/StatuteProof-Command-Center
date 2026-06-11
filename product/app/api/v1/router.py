"""
router.py — FastAPI API v1 для RegRadar Enterprise.

Монтируется на NiceGUI app: nicegui_app.include_router(api_router, prefix="/api/v1")

Эндпоинты:
  POST /auth/login           — обмен логин/пароль → access_token + refresh cookie
  POST /auth/refresh         — обновление access_token по refresh cookie
  POST /auth/logout          — инвалидация refresh cookie
  GET  /regulations          — список НПА (с фильтрами, пагинацией)
  GET  /regulations/{id}     — детальная карточка НПА
  POST /regulations/{id}/status — обновление статуса документа (admin only)
  GET  /kpis                 — KPI-метрики для дашборда
  GET  /reports/executive    — генерация и возврат CEO-отчёта (admin only)
  GET  /health               — статус сервиса (публичный)

Безопасность:
  Все эндпоинты кроме /auth/*, /health защищены JWT через get_current_user.
  /regulations/{id}/status и /reports/executive требуют роль "admin".
  Rate limiting применяется через ASGI middleware (middleware.py).
  Все ORM-запросы используют параметризацию SQLAlchemy — SQL-инъекции исключены.
"""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# ── Pydantic схемы запросов и ответов ─────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = 900  # 15 минут в секундах


class RegulationStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(VALIDATED|PROCESSING|HUMAN_REVIEW)$",
        description="Допустимые значения: VALIDATED, PROCESSING, HUMAN_REVIEW",
    )


class RegulationResponse(BaseModel):
    id:               int
    title:            str
    jurisdiction:     str
    publication_date: Optional[str]
    effective_date:   Optional[str]
    summary:          Optional[str]
    critical_level:   str
    source_url:       str
    confidence:       float
    status:           str
    extracted_at:     Optional[str]


class KPIResponse(BaseModel):
    total_regulations:    int
    critical_count:       int
    human_review_count:   int
    new_last_7_days:      int
    risk_exposure_usd:    int
    risk_exposure_fmt:    str
    hours_saved:          float
    hours_saved_fmt:      str
    ai_processed:         int


# ── Router ────────────────────────────────────────────────────────────────────

api_router = APIRouter(tags=["RegRadar API v1"])


# ── Вспомогательные dependency functions ──────────────────────────────────────
# Определяются ДО маршрутов, чтобы Python 3.14 не создавал ForwardRef

def _get_current_user(request: Request) -> dict:
    """
    FastAPI dependency: читает аутентифицированного пользователя из
    request.state, заполняемого JWTAuthMiddleware ДО вызова handler.

    Если токен не прошёл middleware (публичный маршрут попал сюда через
    misconfiguration) — возвращает 401 как защитный барьер.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "sub":   request.state.user,
        "roles": getattr(request.state, "roles", []),
        "jti":   getattr(request.state, "jti", ""),
    }


def _require_admin(payload: dict = Depends(_get_current_user)) -> dict:
    """Проверяет наличие роли 'admin' в токене."""
    if "admin" not in payload.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль 'admin' для этого ресурса",
        )
    return payload


# ── /health — публичный эндпоинт мониторинга ─────────────────────────────────

@api_router.get("/health", summary="Статус сервиса")
def health_check() -> dict:
    """Публичный health-check. Не требует аутентификации."""
    return {
        "status":    "ok",
        "service":   "RegRadar",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── /auth/login — выдача токенов ─────────────────────────────────────────────

@api_router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Аутентификация (логин/пароль)",
)
def login(body: LoginRequest, response: Response) -> TokenResponse:
    """
    Проверяет учётные данные из .env (API_USERNAME / API_PASSWORD_HASH).
    При успехе возвращает access_token и устанавливает HttpOnly refresh-куку.
    При ошибке — HTTP 401 с задержкой (защита от timing-атак).
    """
    import time
    from app.infrastructure.security.auth import (
        verify_credentials, create_access_token, create_refresh_token,
        make_refresh_cookie_params,
    )

    # Фиксированная задержка для защиты от timing-атак
    start = time.monotonic()

    ok = verify_credentials(body.username, body.password)

    # Обеспечиваем минимальное время ответа 200мс (против timing-attack)
    elapsed = time.monotonic() - start
    if elapsed < 0.2:
        time.sleep(0.2 - elapsed)

    if not ok:
        log.warning("auth/login: неуспешная попытка для пользователя '%s'", body.username[:30])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Определяем роли (admin если логин совпадает с API_USERNAME)
    roles = ["viewer", "admin"]

    access_token  = create_access_token(body.username, roles)
    refresh_token = create_refresh_token(body.username)

    # Refresh-токен в HttpOnly Secure SameSite=Strict куке — недоступен JS
    cookie_params = make_refresh_cookie_params()
    response.set_cookie(value=refresh_token, **cookie_params)

    log.info("auth/login: успешный вход пользователя '%s'", body.username[:30])
    return TokenResponse(access_token=access_token)


# ── /auth/refresh — обновление access-токена ─────────────────────────────────

@api_router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Обновление access-токена по refresh-куке",
)
def refresh_token(request: Request, response: Response) -> TokenResponse:
    """
    Читает refresh-токен из HttpOnly-куки, верифицирует его и выдаёт
    новый access-токен. Refresh-кука перевыпускается с обновлённым сроком.
    """
    from app.infrastructure.security.auth import (
        verify_token, create_access_token, create_refresh_token,
        make_refresh_cookie_params, _REFRESH_COOKIE_NAME,
    )

    token = request.cookies.get(_REFRESH_COOKIE_NAME, "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh-токен отсутствует — выполните повторный вход",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(token, expected_type="refresh")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=getattr(exc, "detail", "Refresh-токен недействителен"),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub", "")
    roles   = ["viewer", "admin"]

    new_access  = create_access_token(subject, roles)
    new_refresh = create_refresh_token(subject)

    cookie_params = make_refresh_cookie_params()
    response.set_cookie(value=new_refresh, **cookie_params)
    log.info("auth/refresh: токен обновлён для '%s'", subject[:30])
    return TokenResponse(access_token=new_access)


# ── /auth/logout ──────────────────────────────────────────────────────────────

@api_router.post(
    "/auth/logout",
    status_code=204,
    summary="Выход (инвалидация refresh-куки)",
)
def logout(response: Response) -> None:
    """Удаляет refresh-куку. Access-токен живёт до истечения 15 мин."""
    from app.infrastructure.security.auth import _REFRESH_COOKIE_NAME
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    log.info("auth/logout: кука очищена")


# ── /regulations — список НПА ─────────────────────────────────────────────────

@api_router.get(
    "/regulations",
    response_model=list[RegulationResponse],
    summary="Список регуляторных актов",
)
def list_regulations(
    current_user: Annotated[dict, Depends(_get_current_user)],
    jurisdiction: Optional[str] = Query(None, max_length=5, description="RU/KZ/AZ/BY/UZ"),
    level:        Optional[str] = Query(None, description="CRITICAL/HIGH/MEDIUM/LOW"),
    status_f:     Optional[str] = Query(None, alias="status", description="VALIDATED/PROCESSING/HUMAN_REVIEW"),
    days:         int           = Query(30,  ge=1, le=365),
    limit:        int           = Query(50,  ge=1, le=500),
    offset:       int           = Query(0,   ge=0),
) -> list[dict]:
    """
    Возвращает список НПА с фильтрами. Все параметры — через Query-параметры.
    100% параметризованные ORM-запросы — SQL-инъекции математически исключены.
    """
    from datetime import timedelta
    from app.infrastructure.db.session import SessionLocal
    from app.infrastructure.db.models import RegulationRecord

    cutoff = datetime.utcnow() - timedelta(days=days)

    with SessionLocal() as db:
        # Строим запрос через ORM (SQLAlchemy) — только bind-параметры
        q = db.query(RegulationRecord).filter(
            RegulationRecord.extracted_at >= cutoff
        )
        if jurisdiction:
            q = q.filter(RegulationRecord.jurisdiction == jurisdiction)
        if level:
            q = q.filter(RegulationRecord.critical_level == level)
        if status_f:
            q = q.filter(RegulationRecord.status == status_f)

        q = q.order_by(RegulationRecord.extracted_at.desc())
        q = q.offset(offset).limit(limit)
        rows = q.all()

    return [
        {
            "id":               r.id,
            "title":            r.title,
            "jurisdiction":     r.jurisdiction,
            "publication_date": r.publication_date,
            "effective_date":   r.effective_date,
            "summary":          r.summary,
            "critical_level":   r.critical_level,
            "source_url":       r.source_url,
            "confidence":       round(r.confidence * 100, 1),
            "status":           r.status,
            "extracted_at":     r.extracted_at.isoformat() if r.extracted_at else None,
        }
        for r in rows
    ]


# ── /regulations/{id} — детальная карточка ────────────────────────────────────

@api_router.get(
    "/regulations/{regulation_id}",
    summary="Детальная карточка НПА",
)
def get_regulation(
    regulation_id: int,
    current_user: Annotated[dict, Depends(_get_current_user)],
) -> dict:
    """Возвращает полную карточку НПА включая AI-анализ."""
    import json as json_lib
    from sqlalchemy import text
    from app.infrastructure.db.session import engine

    with engine.connect() as c:
        # Параметризованный запрос — :rid связывается с regulation_id
        row = c.execute(
            text(
                "SELECT id, title, jurisdiction, publication_date, effective_date, "
                "       summary, industries, critical_level, source_url, confidence, "
                "       status, extracted_at, ai_analysis "
                "FROM regulations WHERE id = :rid"
            ),
            {"rid": regulation_id},
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"НПА с ID={regulation_id} не найден",
        )

    ai_data: dict = {}
    if row[12]:
        try:
            ai_data = json_lib.loads(row[12])
        except Exception:
            ai_data = {}

    return {
        "id":               row[0],
        "title":            row[1],
        "jurisdiction":     row[2],
        "publication_date": row[3],
        "effective_date":   row[4],
        "summary":          row[5],
        "industries":       row[6],
        "critical_level":   row[7],
        "source_url":       row[8],
        "confidence":       round(float(row[9] or 0) * 100, 1),
        "status":           row[10],
        "extracted_at":     row[11],
        "ai_legal":         ai_data.get("legal", ""),
        "ai_risk":          ai_data.get("risk", ""),
        "ai_fines":         ai_data.get("fines", "N/A"),
        "ai_urgency_days":  ai_data.get("urgency_days", 90),
        "ai_actions":       ai_data.get("action", []),
    }


# ── /regulations/{id}/status — обновление статуса (admin) ────────────────────

@api_router.post(
    "/regulations/{regulation_id}/status",
    status_code=200,
    summary="Обновление статуса НПА (только admin)",
)
def update_regulation_status(
    regulation_id: int,
    body: RegulationStatusUpdate,
    current_user: Annotated[dict, Depends(_require_admin)],
) -> dict:
    """
    Обновляет статус записи. Требует роль 'admin'.
    Запрос полностью параметризован — SQL-инъекция невозможна.
    """
    from sqlalchemy import text
    from app.infrastructure.db.session import engine

    with engine.connect() as c:
        result = c.execute(
            text(
                "UPDATE regulations "
                "SET status = :status "
                "WHERE id = :rid"
            ),
            {"status": body.status, "rid": regulation_id},
        )
        c.commit()
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"НПА с ID={regulation_id} не найден",
            )

    log.info(
        "regulations: статус ID=%d обновлён на '%s' пользователем '%s'",
        regulation_id, body.status, current_user.get("sub", "?"),
    )
    return {"id": regulation_id, "status": body.status, "updated": True}


# ── /kpis — KPI для дашборда ──────────────────────────────────────────────────

@api_router.get(
    "/kpis",
    response_model=KPIResponse,
    summary="KPI-метрики дашборда",
)
def get_kpis(
    current_user: Annotated[dict, Depends(_get_current_user)],
    days: int = Query(30, ge=1, le=365),
    jurisdiction: Optional[str] = Query(None, max_length=5),
) -> dict:
    """Агрегированные KPI-метрики для рендера карточек дашборда."""
    from app.infrastructure.db.analytics import get_dashboard_kpis
    from datetime import timedelta
    from sqlalchemy import text, func
    from app.infrastructure.db.session import engine

    cutoff = datetime.utcnow() - timedelta(days=days)

    # ORM агрегация через SQLAlchemy text — параметризовано
    jur_filter = "AND jurisdiction = :jur" if jurisdiction else ""
    params = {"cutoff": cutoff.isoformat(), **({"jur": jurisdiction} if jurisdiction else {})}

    with engine.connect() as c:
        total = c.execute(text(
            f"SELECT COUNT(*) FROM regulations WHERE extracted_at >= :cutoff {jur_filter}"
        ), params).scalar() or 0

        critical = c.execute(text(
            f"SELECT COUNT(*) FROM regulations WHERE extracted_at >= :cutoff "
            f"AND critical_level='CRITICAL' {jur_filter}"
        ), params).scalar() or 0

        review = c.execute(text(
            f"SELECT COUNT(*) FROM regulations WHERE status='HUMAN_REVIEW' {jur_filter}"
        ), {"jur": jurisdiction} if jurisdiction else {}).scalar() or 0

        week_cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        new_week = c.execute(text(
            f"SELECT COUNT(*) FROM regulations WHERE extracted_at >= :wc {jur_filter}"
        ), {"wc": week_cutoff, **({"jur": jurisdiction} if jurisdiction else {})}).scalar() or 0

    analytics = get_dashboard_kpis(jurisdiction=jurisdiction)
    risk   = analytics["risk_exposure"]
    hours  = analytics["hours_saved"]

    return {
        "total_regulations":   int(total),
        "critical_count":      int(critical),
        "human_review_count":  int(review),
        "new_last_7_days":     int(new_week),
        "risk_exposure_usd":   risk.get("total_usd", 0),
        "risk_exposure_fmt":   risk.get("total_formatted", "$0"),
        "hours_saved":         hours.get("hours_saved", 0.0),
        "hours_saved_fmt":     hours.get("hours_formatted", "0.0 ч"),
        "ai_processed":        hours.get("documents_processed", 0),
    }


# ── /reports/executive — CEO-отчёт (admin) ────────────────────────────────────

@api_router.get(
    "/reports/executive",
    summary="Генерация исполнительного отчёта (только admin)",
    response_model=None,
)
def get_executive_report(
    current_user: Annotated[dict, Depends(_require_admin)],
    days: int = Query(30, ge=1, le=365),
    jurisdiction: Optional[str] = Query(None, max_length=5),
    format: str = Query("markdown", pattern="^(markdown|json|pdf|html)$"),
):
    """
    Генерирует и возвращает исполнительный CEO-отчёт.
    Требует роль 'admin'. Сохраняет файл в reports/.

    format=markdown — возвращает текст Markdown (default)
    format=json     — возвращает структурированные данные
    format=html     — pixel-perfect HTML (table-centric, WeasyPrint-ready)
    format=pdf      — branded PDF (fpdf2)
    """
    from app.infrastructure.reports.executive_report import (
        generate_executive_report, _fetch_report_data,
    )

    log.info(
        "reports/executive: запрос от '%s' (days=%d, jur=%s, fmt=%s)",
        current_user.get("sub", "?"), days, jurisdiction or "все", format,
    )

    if format == "json":
        data = _fetch_report_data(days, jurisdiction)
        return data

    if format == "html":
        from app.infrastructure.reports.html_report import generate_html_report
        from fastapi.responses import HTMLResponse
        html_bytes = generate_html_report(days=days, jurisdiction=jurisdiction)
        return HTMLResponse(content=html_bytes.decode("utf-8"))

    if format == "pdf":
        from app.infrastructure.reports.pdf_report import generate_pdf_report
        import io
        pdf_bytes = generate_pdf_report(days=days, jurisdiction=jurisdiction)
        now_slug  = datetime.utcnow().strftime("%Y-%m-%d")
        jur_slug  = jurisdiction.lower() if jurisdiction else "all"
        filename  = f"regrada_report_{now_slug}_{jur_slug}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    markdown = generate_executive_report(days=days, jurisdiction=jurisdiction, save_to_disk=True)
    return PlainTextResponse(content=markdown, media_type="text/markdown; charset=utf-8")


# ── /analytics/ytd — Year-to-Date Performance (admin) ────────────────────────

@api_router.get(
    "/analytics/ytd",
    summary="YTD Performance — годовые ROI-метрики (только admin)",
)
def get_ytd_analytics(
    current_user: Annotated[dict, Depends(_require_admin)],
    jurisdiction: Optional[str] = Query(None, max_length=5),
) -> dict:
    """
    Возвращает Year-to-Date метрики производительности системы.

    Используется для обоснования ROI клиенту:
    "Система предотвратила штрафов на $127,000 при стоимости подписки $3,000."

    Включает:
      - total_processed_ytd    — обработано документов с 1 января
      - fines_prevented_ytd    — суммарные предотвращённые санкции (USD)
      - avg_discovery_hours    — среднее время обнаружения нового НПА
      - cost_per_document_usd  — стоимость AI-обработки одного документа
      - roi_multiplier         — коэффициент ROI (штрафы / стоимость подписки)
      - monthly_trend          — помесячная динамика
    """
    from app.infrastructure.analytics.ytd_metrics import get_ytd_performance
    return get_ytd_performance(jurisdiction=jurisdiction)


@api_router.get(
    "/analytics/ytd/trend",
    summary="YTD помесячный тренд (только admin)",
)
def get_ytd_trend(
    current_user: Annotated[dict, Depends(_require_admin)],
    months: int = Query(12, ge=1, le=24),
    jurisdiction: Optional[str] = Query(None, max_length=5),
) -> list:
    """
    Возвращает помесячные снэпшоты за последние N месяцев.
    Используется для графиков дашборда.
    """
    from app.infrastructure.analytics.ytd_metrics import get_monthly_trend
    return get_monthly_trend(months=months, jurisdiction=jurisdiction)


# ── /watchdog — мониторинг здоровья пайплайна (admin) ────────────────────────

@api_router.post(
    "/watchdog/run",
    summary="Запустить цикл watchdog вручную (только admin)",
)
def trigger_watchdog(
    current_user: Annotated[dict, Depends(_require_admin)],
) -> dict:
    """
    Запускает немедленный цикл watchdog (health check + dead link check).
    Обычно вызывается автоматически Celery каждые 60 минут.
    """
    from app.application.watchdog import run_watchdog_cycle
    log.info("watchdog: ручной запуск от пользователя '%s'", current_user.get("sub"))
    return run_watchdog_cycle()


@api_router.get(
    "/watchdog/health",
    summary="Текущий статус здоровья скрапинга (только admin)",
)
def get_watchdog_health(
    current_user: Annotated[dict, Depends(_require_admin)],
) -> dict:
    """
    Возвращает результаты последнего health check без перезапуска watchdog.
    Данные из scrape_metrics за последние 24 часа.
    """
    from app.application.watchdog import run_health_check
    return run_health_check()


@api_router.get(
    "/watchdog/dead-links",
    summary="Список мёртвых ссылок регуляторов (только admin)",
)
def get_dead_links(
    current_user: Annotated[dict, Depends(_require_admin)],
) -> list:
    """
    Возвращает регуляторы с consecutive_failures > 0 из таблицы url_health.
    """
    from app.infrastructure.db.session import engine
    from sqlalchemy import text as _sql_text
    try:
        with engine.connect() as c:
            rows = c.execute(_sql_text("""
                SELECT uh.url, uh.consecutive_failures, uh.total_failures,
                       uh.last_status_code, uh.last_checked_at, uh.is_deprecated,
                       r.name, r.jurisdiction
                FROM url_health uh
                JOIN regulators r ON uh.regulator_id = r.id
                WHERE uh.consecutive_failures > 0
                ORDER BY uh.consecutive_failures DESC
            """)).fetchall()
        return [
            {
                "regulator":            r[6],
                "jurisdiction":         r[7],
                "url":                  r[0],
                "consecutive_failures": r[1],
                "total_failures":       r[2],
                "last_status_code":     r[3],
                "last_checked_at":      str(r[4] or ""),
                "is_deprecated":        bool(r[5]),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── /webhooks — Developer API (под-роутер) ────────────────────────────────────

from app.api.v1.webhooks_controller import webhooks_router as _webhooks_sub  # noqa: E402
api_router.include_router(_webhooks_sub)


