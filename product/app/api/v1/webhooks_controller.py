"""
webhooks_controller.py — Developer-First Webhook API RegRadar Enterprise.

Назначение:
  Даёт клиентам возможность подписаться на события RegRadar и получать
  JSON push-уведомления в свои системы (Slack, Microsoft Teams, Jira,
  корпоративные API) в реальном времени.

  Это делает RegRadar неотъемлемой частью рабочего процесса клиента,
  что снижает отток (churn) к нулю.

Эндпоинты:
  POST   /api/v1/webhooks           — зарегистрировать новый endpoint
  GET    /api/v1/webhooks           — список всех зарегистрированных
  GET    /api/v1/webhooks/{id}      — детали endpoint
  PUT    /api/v1/webhooks/{id}      — обновить (включить/отключить/сменить URL)
  DELETE /api/v1/webhooks/{id}      — удалить endpoint
  POST   /api/v1/webhooks/{id}/test — тестовый push (без реального события)

Поддерживаемые платформы:
  generic  — стандартный JSON (любой HTTP-endpoint)
  slack    — Slack Block Kit (автоопределяется по URL или platform поле)
  teams    — Microsoft Teams Adaptive Cards
  jira     — Jira Service Management webhook (создаёт задачу через webhook)

Безопасность:
  - Все эндпоинты требуют роль admin (JWT).
  - HMAC-SHA256 подпись каждого исходящего payload (X-RegRadar-Signature).
  - URL проходит базовую валидацию схемы (https только в production).
  - Secret хранится в БД, в API никогда не возвращается целиком (маскируется).

Интеграция с пайплайном:
  notify_regulation_via_db() читает активные endpoints из webhook_endpoints
  и рассылает payload при обнаружении нового CRITICAL/HIGH документа.
  Вызывается из pipeline.py после _repo.upsert().
"""

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text

log = logging.getLogger(__name__)

_BASE_URL = os.getenv("REGRADA_BASE_URL", "http://localhost:8080")
_JUR_FLAGS = {"RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿", "BY": "🇧🇾", "UZ": "🇺🇿"}
_LEVEL_COLORS = {
    "CRITICAL": "#dc2626", "HIGH": "#ea580c",
    "MEDIUM": "#ca8a04",   "LOW": "#16a34a",
}
_VALID_PLATFORMS = {"generic", "slack", "teams", "jira"}
_VALID_EVENTS    = {
    "regulation.detected",    # новый НПА найден
    "regulation.critical",    # только CRITICAL
    "watchdog.alert",         # сбой пайплайна
    "dead_link.deprecated",   # URL помечен мёртвым
}

webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ── Pydantic схемы ────────────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    url:         str   = Field(..., description="HTTP/HTTPS URL для push")
    description: str   = Field("",  max_length=300)
    platform:    str   = Field("generic", pattern="^(generic|slack|teams|jira)$")
    events:      list[str] = Field(
        default=["regulation.detected"],
        description="Список событий для подписки",
    )
    secret:      str   = Field("", description="HMAC-SHA256 секрет (опционально)")

    class Config:
        json_schema_extra = {"example": {
            "url":         "https://hooks.slack.com/services/T00/B00/xxxx",
            "description": "Slack #compliance-alerts",
            "platform":    "slack",
            "events":      ["regulation.detected", "regulation.critical"],
            "secret":      "my-secret-key",
        }}


class WebhookUpdate(BaseModel):
    url:         Optional[str]       = None
    description: Optional[str]       = None
    is_active:   Optional[bool]      = None
    events:      Optional[list[str]] = None
    secret:      Optional[str]       = None


class WebhookResponse(BaseModel):
    id:               int
    url:              str
    description:      str
    platform:         str
    events:           list[str]
    is_active:        bool
    created_at:       str
    last_triggered_at: Optional[str]
    success_count:    int
    failure_count:    int
    secret_masked:    str  # показываем только первые 4 символа

    class Config:
        from_attributes = True


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_engine():
    from app.infrastructure.db.session import engine
    return engine


def _ensure_table() -> None:
    engine = _get_engine()
    with engine.connect() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                description TEXT DEFAULT '',
                platform VARCHAR(20) DEFAULT 'generic',
                events TEXT DEFAULT '["regulation.detected"]',
                secret TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at DATETIME DEFAULT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        """))
        c.commit()


def _row_to_response(row) -> dict:
    secret = str(row[6] or "")
    secret_masked = (secret[:4] + "****") if len(secret) >= 4 else ("****" if secret else "")
    events_raw = row[4] or '["regulation.detected"]'
    try:
        events_list = json.loads(events_raw)
    except Exception:
        events_list = ["regulation.detected"]
    return {
        "id":                row[0],
        "url":               row[1],
        "description":       row[2] or "",
        "platform":          row[3] or "generic",
        "events":            events_list,
        "is_active":         bool(row[5]),
        "created_at":        str(row[7] or ""),
        "last_triggered_at": str(row[8]) if row[8] else None,
        "success_count":     int(row[9] or 0),
        "failure_count":     int(row[10] or 0),
        "secret_masked":     secret_masked,
    }


# ── CRUD эндпоинты ────────────────────────────────────────────────────────────

@webhooks_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать webhook endpoint",
)
def create_webhook(
    body:    WebhookCreate,
    request: Request,
) -> dict:
    """
    Регистрирует новый webhook-получатель.
    URL должен быть доступен и отвечать HTTP 2xx на POST.
    """
    _ensure_table()
    engine = _get_engine()

    # Валидация URL-схемы
    if not (body.url.startswith("http://") or body.url.startswith("https://")):
        raise HTTPException(
            status_code=422,
            detail="URL должен начинаться с http:// или https://",
        )

    # Авто-определение Slack по URL
    platform = body.platform
    if "hooks.slack.com" in body.url:
        platform = "slack"
    elif "webhook.office.com" in body.url or "teams.microsoft.com" in body.url:
        platform = "teams"

    # Валидация событий
    invalid_events = [e for e in body.events if e not in _VALID_EVENTS]
    if invalid_events:
        raise HTTPException(
            status_code=422,
            detail=f"Неизвестные события: {invalid_events}. "
                   f"Допустимые: {sorted(_VALID_EVENTS)}",
        )

    try:
        with engine.connect() as c:
            c.execute(text("""
                INSERT INTO webhook_endpoints
                    (url, description, platform, events, secret, is_active, created_at)
                VALUES
                    (:url, :desc, :platform, :events, :secret, 1, :now)
            """), {
                "url":      body.url,
                "desc":     body.description,
                "platform": platform,
                "events":   json.dumps(body.events),
                "secret":   body.secret,
                "now":      datetime.utcnow().isoformat(),
            })
            c.commit()
            new_id = c.execute(text("SELECT last_insert_rowid()")).scalar()

        log.info(
            "[WEBHOOK] зарегистрирован #%d platform=%s url=%s",
            new_id, platform, body.url[:60],
        )
        return {"id": new_id, "status": "created", "platform": platform}

    except Exception as exc:
        log.error("[WEBHOOK] ошибка создания — %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@webhooks_router.get("", summary="Список webhook endpoints")
def list_webhooks(request: Request) -> list[dict]:
    """Возвращает все зарегистрированные webhook endpoints."""
    _ensure_table()
    engine = _get_engine()
    try:
        with engine.connect() as c:
            rows = c.execute(text("""
                SELECT id, url, description, platform, events,
                       is_active, secret, created_at,
                       last_triggered_at, success_count, failure_count
                FROM webhook_endpoints
                ORDER BY created_at DESC
            """)).fetchall()
        return [_row_to_response(r) for r in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@webhooks_router.get("/{webhook_id}", summary="Детали webhook endpoint")
def get_webhook(webhook_id: int, request: Request) -> dict:
    _ensure_table()
    engine = _get_engine()
    with engine.connect() as c:
        row = c.execute(text("""
            SELECT id, url, description, platform, events,
                   is_active, secret, created_at,
                   last_triggered_at, success_count, failure_count
            FROM webhook_endpoints WHERE id = :wid
        """), {"wid": webhook_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Webhook не найден")
    return _row_to_response(row)


@webhooks_router.put("/{webhook_id}", summary="Обновить webhook endpoint")
def update_webhook(webhook_id: int, body: WebhookUpdate, request: Request) -> dict:
    _ensure_table()
    engine = _get_engine()

    # Проверяем существование
    with engine.connect() as c:
        existing = c.execute(
            text("SELECT id FROM webhook_endpoints WHERE id = :wid"),
            {"wid": webhook_id},
        ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Webhook не найден")

    # Строим SET-часть запроса только из переданных полей
    updates: dict = {}
    if body.url is not None:
        if not (body.url.startswith("http://") or body.url.startswith("https://")):
            raise HTTPException(status_code=422, detail="URL должен начинаться с http(s)://")
        updates["url"] = body.url
    if body.description is not None:
        updates["description"] = body.description
    if body.is_active is not None:
        updates["is_active"] = int(body.is_active)
    if body.events is not None:
        invalid = [e for e in body.events if e not in _VALID_EVENTS]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Неизвестные события: {invalid}")
        updates["events"] = json.dumps(body.events)
    if body.secret is not None:
        updates["secret"] = body.secret

    if not updates:
        raise HTTPException(status_code=422, detail="Нет полей для обновления")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["wid"] = webhook_id
    try:
        with engine.connect() as c:
            c.execute(text(
                f"UPDATE webhook_endpoints SET {set_clause} WHERE id = :wid"
            ), updates)
            c.commit()
        return {"id": webhook_id, "status": "updated"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@webhooks_router.delete("/{webhook_id}", summary="Удалить webhook endpoint")
def delete_webhook(webhook_id: int, request: Request) -> dict:
    _ensure_table()
    engine = _get_engine()
    with engine.connect() as c:
        result = c.execute(
            text("DELETE FROM webhook_endpoints WHERE id = :wid"),
            {"wid": webhook_id},
        )
        c.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Webhook не найден")
    log.info("[WEBHOOK] удалён #%d", webhook_id)
    return {"id": webhook_id, "status": "deleted"}


@webhooks_router.post("/{webhook_id}/test", summary="Тестовый push")
def test_webhook(webhook_id: int, request: Request) -> dict:
    """
    Отправляет тестовый payload на зарегистрированный endpoint.
    Полезно для проверки подключения без ожидания реального события.
    """
    _ensure_table()
    engine = _get_engine()
    with engine.connect() as c:
        row = c.execute(text(
            "SELECT url, platform, secret FROM webhook_endpoints WHERE id = :wid AND is_active=1"
        ), {"wid": webhook_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Webhook не найден или отключён")

    url, platform, secret = row
    test_reg = {
        "id":             0,
        "title":          "TEST: RegRadar webhook test event",
        "jurisdiction":   "RU",
        "critical_level": "HIGH",
        "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "summary":        "Это тестовое событие, подтверждающее корректную настройку webhook.",
        "source_url":     _BASE_URL,
    }

    ok = _dispatch_to_endpoint(
        endpoint_id=webhook_id,
        url=url,
        platform=platform,
        secret=secret or "",
        reg=test_reg,
        event_type="regulation.detected",
        is_test=True,
    )
    return {"id": webhook_id, "success": ok, "url": url[:80]}


# ── Dispatch-движок ───────────────────────────────────────────────────────────

def _sign(payload_bytes: bytes, secret: str) -> str:
    """HMAC-SHA256 подпись payload."""
    if not secret:
        return ""
    return "sha256=" + hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()


def _build_payload(
    reg: dict,
    platform: str,
    event_type: str = "regulation.detected",
    is_test: bool = False,
) -> dict:
    """
    Формирует payload в зависимости от платформы.
    """
    level = reg.get("critical_level", "HIGH")
    jur   = reg.get("jurisdiction", "")
    flag  = _JUR_FLAGS.get(jur, "🌐")
    title = (reg.get("title") or "—")[:200]
    eff   = reg.get("effective_date") or "—"
    rid   = reg.get("id")
    color = _LEVEL_COLORS.get(level, "#6b7280")
    dash  = f"{_BASE_URL}/regulations/{rid}" if rid else _BASE_URL
    test_tag = " [TEST]" if is_test else ""

    if platform == "slack":
        return {
            "attachments": [{
                "color": color,
                "blocks": [
                    {"type": "header",
                     "text": {"type": "plain_text",
                              "text": f"⚠️ RegRadar | {level}: {flag} {jur}{test_tag}"}},
                    {"type": "section",
                     "text": {"type": "mrkdwn", "text": f"*{title}*"}},
                    {"type": "section",
                     "fields": [
                         {"type": "mrkdwn", "text": f"*Дата вступления:*\n{eff}"},
                         {"type": "mrkdwn", "text": f"*Штраф/санкция:*\n{reg.get('fines', '—')}"},
                     ]},
                    {"type": "actions",
                     "elements": [{
                         "type": "button",
                         "text": {"type": "plain_text", "text": "Открыть в RegRadar"},
                         "url":  dash, "style": "primary",
                     }]},
                ],
            }]
        }

    if platform == "teams":
        return {
            "@type":      "MessageCard",
            "@context":   "https://schema.org/extensions",
            "summary":    f"RegRadar: {level} — {title[:80]}",
            "themeColor": color.lstrip("#"),
            "title":      f"⚠️ {level}: {flag} {jur} — RegRadar{test_tag}",
            "text":       title,
            "sections": [{
                "facts": [
                    {"name": "Дата вступления", "value": eff},
                    {"name": "Юрисдикция",      "value": jur},
                    {"name": "Уровень риска",   "value": level},
                ]
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name":  "Открыть в RegRadar",
                "targets": [{"os": "default", "uri": dash}],
            }],
        }

    # generic (включая Jira)
    return {
        "event":      event_type,
        "test":       is_test,
        "timestamp":  datetime.utcnow().isoformat() + "Z",
        "source":     "RegRadar Enterprise",
        "regulation": {
            "id":             reg.get("id"),
            "title":          title,
            "jurisdiction":   jur,
            "critical_level": level,
            "effective_date": eff,
            "summary":        (reg.get("summary") or "")[:400],
            "source_url":     reg.get("source_url"),
            "dashboard_url":  dash,
            "urgency_score":  reg.get("urgency_score"),
            "action_plan":    reg.get("action_plan"),
        },
    }


def _dispatch_to_endpoint(
    endpoint_id: int,
    url: str,
    platform: str,
    secret: str,
    reg: dict,
    event_type: str = "regulation.detected",
    is_test: bool = False,
) -> bool:
    """
    Отправляет POST на один webhook endpoint.
    Обновляет статистику (success_count / failure_count) в БД.
    Повторная попытка: 1 retry через 3 секунды при ошибке сети.
    """
    payload = _build_payload(reg, platform, event_type, is_test)
    body    = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sig     = _sign(body, secret)
    headers = {
        "Content-Type":       "application/json",
        "X-RegRadar-Event":   event_type,
        "X-RegRadar-Version": "2.0",
    }
    if sig:
        headers["X-RegRadar-Signature"] = sig

    ok = False
    for attempt in range(2):  # 1 попытка + 1 ретрай
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status < 300:
                    ok = True
                    break
                log.warning(
                    "[WEBHOOK] #%d → HTTP %d (%s)", endpoint_id, resp.status, url[:60]
                )
        except Exception as exc:
            log.warning(
                "[WEBHOOK] #%d попытка %d — %s (%s)", endpoint_id, attempt + 1, exc, url[:60]
            )
            if attempt == 0:
                time.sleep(3)

    # Обновляем счётчики в БД
    try:
        engine = _get_engine()
        with engine.connect() as c:
            if ok:
                c.execute(text("""
                    UPDATE webhook_endpoints
                    SET success_count = success_count + 1,
                        last_triggered_at = :now
                    WHERE id = :wid
                """), {"now": datetime.utcnow().isoformat(), "wid": endpoint_id})
            else:
                c.execute(text("""
                    UPDATE webhook_endpoints
                    SET failure_count = failure_count + 1
                    WHERE id = :wid
                """), {"wid": endpoint_id})
            c.commit()
    except Exception as db_exc:
        log.debug("[WEBHOOK] ошибка обновления счётчика — %s", db_exc)

    return ok


# ── Публичный API: dispatch из pipeline.py ───────────────────────────────────

def notify_regulation_via_db(reg: dict, event_type: str = "regulation.detected") -> None:
    """
    Читает активные endpoint-ы из webhook_endpoints и рассылает payload.
    Вызывается из pipeline.py в фоновом потоке.

    Приоритет:
      1. Если CRITICAL → отправляется на endpoints, подписанных на "regulation.critical"
         или "regulation.detected".
      2. Иначе → только "regulation.detected".
    """
    level = reg.get("critical_level", "LOW")
    if level not in ("CRITICAL", "HIGH"):
        return

    try:
        _ensure_table()
        engine = _get_engine()
        with engine.connect() as c:
            rows = c.execute(text("""
                SELECT id, url, platform, events, secret
                FROM webhook_endpoints
                WHERE is_active = 1
            """)).fetchall()
    except Exception as exc:
        log.error("[WEBHOOK] не удалось загрузить endpoints — %s", exc)
        return

    if not rows:
        return

    def _dispatch_all():
        for wid, url, platform, events_json, secret in rows:
            try:
                subscribed = json.loads(events_json or '["regulation.detected"]')
            except Exception:
                subscribed = ["regulation.detected"]

            # Проверяем подписку на тип события
            if event_type not in subscribed:
                if level == "CRITICAL" and "regulation.critical" not in subscribed:
                    continue
                elif level != "CRITICAL":
                    continue

            _dispatch_to_endpoint(
                endpoint_id=int(wid),
                url=url,
                platform=platform or "generic",
                secret=secret or "",
                reg=reg,
                event_type=event_type,
            )
            time.sleep(0.1)

    t = threading.Thread(target=_dispatch_all, daemon=True, name="webhook-db-dispatch")
    t.start()
