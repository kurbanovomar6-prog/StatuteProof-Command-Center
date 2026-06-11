"""
rate_limiter.py — Redis-backed Token Bucket Rate Limiter для RegRadar.

Алгоритм: Token Bucket (скользящее окно, атомарный через Lua-скрипт в Redis).
Транспорт: Redis (primary) → in-memory threading.Lock dict (fallback при отсутствии Redis).

Лимиты по типу маршрута:
  "standard" — данные, поиск:        10 req/sec  на IP
  "admin"    — мутации, статусы, auth: 3 req/min   на IP

Ответ на превышение: HTTP 429 Too Many Requests
Заголовки в ответе:
  X-RateLimit-Limit     — ёмкость корзины
  X-RateLimit-Remaining — остаток токенов
  X-RateLimit-Reset     — Unix timestamp сброса
  Retry-After           — секунд до следующей попытки (только при 429)

Lua-скрипт для Redis: атомарная операция EVAL, исключает гонку состояний
между проверкой и обновлением токенов (невозможна при чистом Python + Redis pipeline).
"""

import logging
import threading
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)

# ── Конфигурация лимитов по типу маршрута ─────────────────────────────────────
@dataclass
class _RouteLimit:
    capacity:    int    # максимальное количество токенов в корзине
    rate_per_sec: float  # скорость пополнения токенов (токенов/сек)

_ROUTE_LIMITS: dict[str, _RouteLimit] = {
    # Стандартные запросы: 10 в секунду на IP
    "standard": _RouteLimit(capacity=10, rate_per_sec=10.0),
    # Административные и мутирующие маршруты: 3 в минуту на IP
    "admin":    _RouteLimit(capacity=3,  rate_per_sec=3.0 / 60.0),
}

# ── Lua-скрипт для атомарного Token Bucket в Redis ────────────────────────────
# Выполняется в одной транзакции через EVAL — невозможна гонка состояний.
# KEYS[1] — ключ записи в Redis (ip:route_type)
# ARGV[1] — capacity (целое)
# ARGV[2] — rate_per_sec (float)
# ARGV[3] — текущее время (float, секунды)
# Возвращает таблицу: {allowed (0/1), remaining_tokens (float), reset_at (float)}
_LUA_TOKEN_BUCKET = """
local key          = KEYS[1]
local capacity     = tonumber(ARGV[1])
local rate         = tonumber(ARGV[2])
local now          = tonumber(ARGV[3])
local ttl          = math.ceil(capacity / rate) + 10

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local last_ts = tonumber(data[2])

-- Инициализация первого обращения
if tokens == nil or last_ts == nil then
    tokens  = capacity - 1
    last_ts = now
    redis.call('HMSET', key, 'tokens', tokens, 'ts', last_ts)
    redis.call('EXPIRE', key, ttl)
    return {1, tokens, now + (capacity / rate)}
end

-- Восполнение токенов пропорционально времени
local elapsed = now - last_ts
local refill  = elapsed * rate
tokens = math.min(capacity, tokens + refill)
last_ts = now

if tokens < 1 then
    -- Корзина пуста — вычисляем время до следующего токена
    local reset_at = now + ((1 - tokens) / rate)
    redis.call('HMSET', key, 'tokens', tokens, 'ts', last_ts)
    redis.call('EXPIRE', key, ttl)
    return {0, 0, reset_at}
end

-- Разрешаем запрос — списываем один токен
tokens = tokens - 1
redis.call('HMSET', key, 'tokens', tokens, 'ts', last_ts)
redis.call('EXPIRE', key, ttl)
return {1, tokens, now + ((capacity - tokens) / rate)}
"""


# ── In-memory Token Bucket (fallback без Redis) ───────────────────────────────

@dataclass
class _Bucket:
    tokens:  float
    last_ts: float


class _InMemoryBucket:
    """
    Потокобезопасный in-memory Token Bucket.
    Используется как fallback когда Redis недоступен.
    При высокой нагрузке рекомендуется Redis — этот вариант не масштабируется на кластер.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, _Bucket] = {}
        self._lock    = threading.Lock()

    def check(self, key: str, capacity: int, rate: float) -> tuple[bool, float, float]:
        """
        Проверяет и списывает токен.
        Возвращает (allowed, remaining_tokens, reset_at_epoch).
        """
        now = time.monotonic()
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = _Bucket(tokens=capacity - 1, last_ts=now)
                reset_at = now + capacity / rate
                return True, float(capacity - 1), reset_at

            b = self._buckets[key]
            # Восполнение токенов
            elapsed  = now - b.last_ts
            b.tokens = min(float(capacity), b.tokens + elapsed * rate)
            b.last_ts = now

            if b.tokens < 1.0:
                reset_at = now + (1.0 - b.tokens) / rate
                return False, 0.0, reset_at

            b.tokens -= 1.0
            reset_at = now + (capacity - b.tokens) / rate
            return True, b.tokens, reset_at

    def cleanup(self, max_age_sec: float = 300.0) -> int:
        """Удаляет просроченные записи из памяти — вызывать периодически."""
        now = time.monotonic()
        with self._lock:
            stale = [k for k, b in self._buckets.items() if now - b.last_ts > max_age_sec]
            for k in stale:
                del self._buckets[k]
        return len(stale)


# ── Основной Rate Limiter ──────────────────────────────────────────────────────

class TokenBucketRateLimiter:
    """
    Redis-backed Token Bucket Rate Limiter с in-memory fallback.

    Использование:
        limiter = TokenBucketRateLimiter(redis_url="redis://localhost:6379/0")
        allowed, headers = limiter.check(ip="1.2.3.4", route_type="standard")
        if not allowed:
            return JSONResponse(status_code=429, headers=headers)
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis    = None
        self._script   = None
        self._memory   = _InMemoryBucket()
        self._using_redis = False

        if redis_url:
            self._connect_redis(redis_url)

    def _connect_redis(self, redis_url: str) -> None:
        """Подключение к Redis. Тихо переходит на in-memory при ошибке."""
        try:
            import redis as redis_lib
            client = redis_lib.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=1,
            )
            client.ping()
            # Регистрируем Lua-скрипт через SCRIPT LOAD для повторного использования
            self._script  = client.register_script(_LUA_TOKEN_BUCKET)
            self._redis   = client
            self._using_redis = True
            log.info("rate_limiter: подключён Redis %s", redis_url[:40])
        except Exception as exc:
            log.warning(
                "rate_limiter: Redis недоступен (%s) — используем in-memory fallback",
                str(exc)[:60],
            )

    def check(self, ip: str, route_type: str = "standard") -> tuple[bool, dict]:
        """
        Проверяет лимит запросов для IP.

        Параметры:
          ip         — клиентский IP-адрес
          route_type — "standard" | "admin"

        Возвращает (allowed: bool, response_headers: dict).
        При allowed=False заголовки включают Retry-After.
        """
        limit = _ROUTE_LIMITS.get(route_type, _ROUTE_LIMITS["standard"])
        key   = f"rr:rl:{route_type}:{ip}"

        if self._using_redis and self._redis and self._script:
            allowed, remaining, reset_at = self._check_redis(key, limit)
        else:
            allowed, remaining, reset_at = self._memory.check(
                key, limit.capacity, limit.rate_per_sec
            )
            # Конвертируем monotonic → wall clock для заголовков
            reset_at_wall = time.time() + (reset_at - time.monotonic())
            reset_at = reset_at_wall

        headers = {
            "X-RateLimit-Limit":     str(limit.capacity),
            "X-RateLimit-Remaining": str(int(remaining)),
            "X-RateLimit-Reset":     str(int(reset_at)),
        }
        if not allowed:
            retry_after = max(1, int(reset_at - time.time()))
            headers["Retry-After"] = str(retry_after)

        return allowed, headers

    def _check_redis(
        self, key: str, limit: _RouteLimit
    ) -> tuple[bool, float, float]:
        """
        Вызывает Lua-скрипт атомарной Token Bucket операции в Redis.
        При ошибке Redis — переходит на in-memory fallback.
        """
        try:
            now    = time.time()
            result = self._script(
                keys=[key],
                args=[str(limit.capacity), str(limit.rate_per_sec), str(now)],
            )
            allowed   = bool(result[0])
            remaining = float(result[1])
            reset_at  = float(result[2])
            return allowed, remaining, reset_at

        except Exception as exc:
            log.warning(
                "rate_limiter: Redis ошибка (%s) — переключаемся на in-memory",
                str(exc)[:60],
            )
            self._using_redis = False
            allowed, remaining, reset_at_mono = self._memory.check(
                key, limit.capacity, limit.rate_per_sec
            )
            return allowed, remaining, time.time() + (reset_at_mono - time.monotonic())


# ── Маппинг маршрутов → типы лимитов ──────────────────────────────────────────
# Используется middleware для определения лимита по URL prefix.

def classify_route(path: str) -> str:
    """
    Определяет тип лимита по пути запроса.

    Административные маршруты (3 req/min):
      /api/v1/auth/*
      /api/v1/reg/status*
      /api/v1/reports/*

    Стандартные маршруты (10 req/sec):
      всё остальное в /api/*
    """
    _ADMIN_PREFIXES = (
        "/api/v1/auth/",
        "/api/v1/reg/status",
        "/api/v1/reports/",
        "/api/v1/admin/",
    )
    for prefix in _ADMIN_PREFIXES:
        if path.startswith(prefix):
            return "admin"
    return "standard"


# Глобальный синглтон — инициализируется в lifespan приложения
_global_limiter: TokenBucketRateLimiter | None = None


def get_limiter() -> TokenBucketRateLimiter:
    """Возвращает глобальный экземпляр лимитера. Инициализирует при первом вызове."""
    global _global_limiter
    if _global_limiter is None:
        import os
        redis_url = os.getenv("REDIS_URL", "")
        _global_limiter = TokenBucketRateLimiter(redis_url=redis_url or None)
    return _global_limiter
