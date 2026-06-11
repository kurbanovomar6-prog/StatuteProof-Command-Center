"""
auth.py — Асимметричная JWT-аутентификация для RegRadar Enterprise.

Алгоритм: RS256 (RSA 4096-bit) — единственный ключ не покидает сервер.
Токены:
  access_token  — срок жизни 15 минут, передаётся в заголовке Authorization.
  refresh_token — срок жизни 7 дней, хранится в HttpOnly + Secure + SameSite=Strict cookie.
                  XSS-атаки математически лишены доступа к refresh-токену.

Структура payload access-токена:
  sub   — идентификатор субъекта (логин пользователя)
  roles — список ролей: ["viewer"] / ["viewer", "admin"]
  type  — "access" | "refresh"
  iat   — issued at (UTC timestamp)
  exp   — expiry (UTC timestamp)
  jti   — JWT ID (UUIDv4, уникален для каждого токена — для реализации blacklist)

Генерация ключей:
  При первом запуске автоматически создаётся RSA 4096-bit ключевая пара
  в директории keys/ (исключена из git через .gitignore).
  Приватный ключ: keys/private.pem (chmod 600)
  Публичный ключ: keys/public.pem (читается верификаторами)
"""

import os
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

log = logging.getLogger(__name__)

# ── Параметры токенов ──────────────────────────────────────────────────────────
_ACCESS_TOKEN_EXPIRE_MINUTES  = 15
_REFRESH_TOKEN_EXPIRE_DAYS    = 7
_ALGORITHM                    = "RS256"
_REFRESH_COOKIE_NAME          = "rr_refresh"

# ── Пути к ключам (из переменных окружения или по умолчанию) ──────────────────
_KEYS_DIR         = Path(os.getenv("JWT_KEYS_DIR", "keys"))
_PRIVATE_KEY_PATH = _KEYS_DIR / "private.pem"
_PUBLIC_KEY_PATH  = _KEYS_DIR / "public.pem"


def _generate_rsa_keypair() -> None:
    """
    Генерирует RSA 4096-bit ключевую пару и сохраняет на диск.
    Вызывается один раз — при первом запуске без существующих ключей.
    Приватный ключ получает права 600 (только владелец-процесс).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
    except ImportError as exc:
        raise RuntimeError(
            "Пакет 'cryptography' не установлен. "
            "Выполните: pip install cryptography"
        ) from exc

    _KEYS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    # Генерация ключей RSA-4096
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend(),
    )
    public_key = private_key.public_key()

    # Сериализация приватного ключа (PKCS8, без пароля — пароль на уровне FS)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    _PRIVATE_KEY_PATH.write_bytes(priv_pem)
    _PUBLIC_KEY_PATH.write_bytes(pub_pem)

    # Ограничиваем права: только процесс-владелец
    os.chmod(_PRIVATE_KEY_PATH, 0o600)
    os.chmod(_PUBLIC_KEY_PATH,  0o644)

    log.info(
        "auth: RSA-4096 ключевая пара сгенерирована → %s / %s",
        _PRIVATE_KEY_PATH, _PUBLIC_KEY_PATH,
    )


def _load_private_key() -> str:
    """Загружает PEM-строку приватного ключа с диска."""
    if not _PRIVATE_KEY_PATH.exists():
        log.warning("auth: приватный ключ не найден — генерируем новую пару")
        _generate_rsa_keypair()
    return _PRIVATE_KEY_PATH.read_text(encoding="utf-8")


def _load_public_key() -> str:
    """Загружает PEM-строку публичного ключа с диска."""
    if not _PUBLIC_KEY_PATH.exists():
        _generate_rsa_keypair()
    return _PUBLIC_KEY_PATH.read_text(encoding="utf-8")


# Кэшированные ключи (загружаются один раз при старте)
_PRIVATE_KEY_PEM: str = ""
_PUBLIC_KEY_PEM:  str = ""


def _ensure_keys() -> None:
    """Инициализирует глобальный кэш ключей — вызывается из lifespan."""
    global _PRIVATE_KEY_PEM, _PUBLIC_KEY_PEM
    if not _PRIVATE_KEY_PEM:
        _PRIVATE_KEY_PEM = _load_private_key()
        _PUBLIC_KEY_PEM  = _load_public_key()


# ── Генерация токенов ──────────────────────────────────────────────────────────

def create_access_token(subject: str, roles: list[str]) -> str:
    """
    Создаёт подписанный RS256 access-токен.
    Срок жизни: ACCESS_TOKEN_EXPIRE_MINUTES (15 мин).

    Параметры:
      subject — идентификатор пользователя (логин)
      roles   — список ролей (["viewer"] / ["viewer", "admin"])
    """
    _ensure_keys()
    try:
        from jose import jwt
    except ImportError as exc:
        raise RuntimeError("pip install 'python-jose[cryptography]'") from exc

    now    = datetime.utcnow()
    expire = now + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":   subject,
        "roles": roles,
        "type":  "access",
        "iat":   now,
        "exp":   expire,
        "jti":   str(uuid.uuid4()),
    }
    return jwt.encode(payload, _PRIVATE_KEY_PEM, algorithm=_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Создаёт подписанный RS256 refresh-токен.
    Срок жизни: REFRESH_TOKEN_EXPIRE_DAYS (7 дней).
    Предназначен для HttpOnly-куки, не раскрывается JS.
    """
    _ensure_keys()
    try:
        from jose import jwt
    except ImportError as exc:
        raise RuntimeError("pip install 'python-jose[cryptography]'") from exc

    now    = datetime.utcnow()
    expire = now + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":  subject,
        "type": "refresh",
        "iat":  now,
        "exp":  expire,
        "jti":  str(uuid.uuid4()),
    }
    return jwt.encode(payload, _PRIVATE_KEY_PEM, algorithm=_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Верифицирует JWT-токен подписью RS256 публичным ключом.
    Проверяет: подпись, срок жизни, тип токена.

    Возвращает декодированный payload или выбрасывает HTTPException 401.
    """
    _ensure_keys()
    try:
        from jose import jwt, JWTError, ExpiredSignatureError
    except ImportError as exc:
        raise RuntimeError("pip install 'python-jose[cryptography]'") from exc

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Токен недействителен или просрочен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _PUBLIC_KEY_PEM, algorithms=[_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен просрочен — выполните повторный вход",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        log.warning("auth: ошибка верификации JWT — %s", exc)
        raise credentials_exception

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ожидался токен типа '{expected_type}', получен '{payload.get('type')}'",
        )

    return payload


def require_role(required_role: str):
    """
    FastAPI dependency-фабрика: проверяет наличие роли в токене.
    Использование: Depends(require_role("admin"))
    """
    def _check(payload: dict = Depends(get_current_user)) -> dict:
        roles: list[str] = payload.get("roles", [])
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Роль '{required_role}' требуется для этого ресурса",
            )
        return payload
    return _check


# ── FastAPI Security scheme ────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> dict:
    """
    FastAPI dependency: извлекает и верифицирует Bearer-токен из заголовка Authorization.
    Внедряется как Depends(get_current_user) во все защищённые эндпоинты.
    """
    return verify_token(credentials.credentials, expected_type="access")


def get_refresh_token_from_cookie(request: Request) -> str:
    """Извлекает refresh-токен из HttpOnly-куки. Выбрасывает 401 если отсутствует."""
    token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh-токен отсутствует. Выполните повторный вход.",
        )
    return token


def make_refresh_cookie_params() -> dict:
    """
    Возвращает параметры для set_cookie() с максимальной безопасностью:
      httponly=True   — JavaScript не имеет доступа к куке (блокирует XSS)
      secure=True     — кука передаётся только по HTTPS
      samesite=strict — блокирует CSRF-атаки
    """
    return {
        "key":      _REFRESH_COOKIE_NAME,
        "httponly": True,
        "secure":   True,
        "samesite": "strict",
        "max_age":  _REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        "path":     "/api/v1/auth",
    }


# ── Верификация учётных данных ─────────────────────────────────────────────────

def verify_credentials(username: str, password: str) -> bool:
    """
    Проверяет пару логин/пароль против значений из .env.
    Пароль хранится в виде bcrypt-хэша в API_PASSWORD_HASH.
    При пустом хэше — отказ во входе (безопасный default).
    """
    try:
        import bcrypt
    except ImportError as exc:
        raise RuntimeError("pip install bcrypt") from exc

    expected_username = os.getenv("API_USERNAME", "admin")
    password_hash     = os.getenv("API_PASSWORD_HASH", "")

    if not password_hash:
        log.error(
            "auth: API_PASSWORD_HASH не задан в .env — аутентификация отключена"
        )
        return False

    if username != expected_username:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception as exc:
        log.error("auth: ошибка bcrypt checkpw — %s", exc)
        return False
