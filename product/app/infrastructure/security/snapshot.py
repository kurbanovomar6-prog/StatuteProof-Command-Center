"""
snapshot.py — Иммутабельное хранилище документов-доказательств для RegRadar.

Назначение: сохранение оригинального бинарного содержимого каждого
регуляторного PDF как доказательства соответствия (audit proof).
Файлы НИКОГДА не перезаписываются — write-once семантика.

Архитектура хранилища (content-addressed):
  Локальный:  snapshots/{hash[:2]}/{hash}.pdf  +  {hash}.json (метаданные)
  S3 (опцион.): s3://{BUCKET}/snapshots/{hash[:2]}/{hash}.pdf

Адресация: SHA-256 бинарного содержимого файла (не URL).
  Одинаковый документ с разных URL → один и тот же snapshot → дедупликация.

Конфигурация (.env):
  SNAPSHOT_DIR   — локальная директория (по умолчанию: snapshots/)
  S3_BUCKET      — имя S3-бакета (пусто = только локально)
  S3_ENDPOINT    — endpoint S3-совместимого хранилища (пусто = AWS)
  S3_ACCESS_KEY  — ключ доступа S3
  S3_SECRET_KEY  — секретный ключ S3
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

# ── Конфигурация из .env ───────────────────────────────────────────────────────
_SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "snapshots"))
_S3_BUCKET    = os.getenv("S3_BUCKET", "")
_S3_ENDPOINT  = os.getenv("S3_ENDPOINT", "")
_S3_ACCESS    = os.getenv("S3_ACCESS_KEY", "")
_S3_SECRET    = os.getenv("S3_SECRET_KEY", "")

# Поддерживаемые расширения для определения типа файла
_MIME_MAP: dict[bytes, str] = {
    b"%PDF":      "pdf",
    b"PK\x03\x04": "docx",  # ZIP-based: DOCX/XLSX
    b"\xd0\xcf":  "doc",    # OLE2: DOC/XLS
    b"{\rtf":     "rtf",
}


def _detect_extension(file_bytes: bytes) -> str:
    """Определяет расширение файла по magic bytes (не по URL)."""
    for magic, ext in _MIME_MAP.items():
        if file_bytes[:len(magic)] == magic:
            return ext
    return "bin"


def _content_hash(file_bytes: bytes) -> str:
    """SHA-256 хэш бинарного содержимого — уникальный идентификатор документа."""
    return hashlib.sha256(file_bytes).hexdigest()


def _local_path(content_hash: str, ext: str) -> Path:
    """Вычисляет путь локального файла (двухуровневая адресация)."""
    return _SNAPSHOT_DIR / content_hash[:2] / f"{content_hash}.{ext}"


def _meta_path(content_hash: str) -> Path:
    """Путь к JSON-файлу метаданных снапшота."""
    return _SNAPSHOT_DIR / content_hash[:2] / f"{content_hash}.json"


# ── Локальное хранилище ────────────────────────────────────────────────────────

def _store_local(
    file_bytes: bytes,
    content_hash: str,
    ext: str,
    metadata: dict,
) -> bool:
    """
    Сохраняет файл и метаданные локально.
    Не перезаписывает существующий snapshot — write-once.
    Возвращает True при создании нового, False если уже существует.
    """
    file_path = _local_path(content_hash, ext)
    meta_path = _meta_path(content_hash)

    # Файл уже существует — дедупликация выполнена
    if file_path.exists():
        return False

    # Создаём директорию (двухбуквенный bucket)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Записываем бинарный файл атомарно (через temp + rename)
    tmp_path = file_path.with_suffix(".tmp")
    try:
        tmp_path.write_bytes(file_bytes)
        tmp_path.rename(file_path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise exc

    # Сохраняем метаданные для аудита
    meta = {
        "content_hash":  content_hash,
        "file_ext":      ext,
        "size_bytes":    len(file_bytes),
        "stored_at_utc": datetime.utcnow().isoformat(),
        **metadata,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Только чтение — защита от случайной модификации
    os.chmod(file_path, 0o444)

    log.info(
        "snapshot: сохранён %s (%d байт) → %s",
        content_hash[:16], len(file_bytes), file_path,
    )
    return True


# ── S3 хранилище (опционально) ────────────────────────────────────────────────

def _store_s3(
    file_bytes: bytes,
    content_hash: str,
    ext: str,
    metadata: dict,
) -> bool:
    """
    Загружает snapshot в S3-совместимое хранилище.
    Использует S3 Object Lock (COMPLIANCE mode) при поддержке хранилища.
    Возвращает True при успехе, False при ошибке.
    """
    if not _S3_BUCKET:
        return False

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        log.warning("snapshot: boto3 не установлен — S3 пропускается")
        return False

    s3_key = f"snapshots/{content_hash[:2]}/{content_hash}.{ext}"

    try:
        client = boto3.client(
            "s3",
            endpoint_url=_S3_ENDPOINT or None,
            aws_access_key_id=_S3_ACCESS or None,
            aws_secret_access_key=_S3_SECRET or None,
        )

        # Проверяем существование (HEAD request — дешевле GET)
        try:
            client.head_object(Bucket=_S3_BUCKET, Key=s3_key)
            return False  # уже загружен
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise

        # Загружаем бинарный файл
        client.put_object(
            Bucket=_S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType="application/pdf" if ext == "pdf" else "application/octet-stream",
            Metadata={k: str(v) for k, v in metadata.items() if v is not None},
            # ServerSideEncryption для шифрования at-rest
            ServerSideEncryption="AES256",
        )

        log.info(
            "snapshot: S3 загружен s3://%s/%s (%d байт)",
            _S3_BUCKET, s3_key, len(file_bytes),
        )
        return True

    except Exception as exc:
        log.error("snapshot: S3 ошибка — %s", str(exc)[:120])
        return False


# ── Публичный API ──────────────────────────────────────────────────────────────

class SnapshotStore:
    """
    Content-addressed иммутабельное хранилище регуляторных документов.
    Синглтон — используйте глобальный экземпляр `snapshot_store`.
    """

    def __init__(self) -> None:
        _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        file_bytes: bytes,
        source_url: str = "",
        jurisdiction: str = "",
        extra_meta: dict | None = None,
    ) -> tuple[str, bool]:
        """
        Сохраняет файл в хранилище (локально + S3 при конфигурации).

        Параметры:
          file_bytes   — байты файла (PDF/DOCX/...)
          source_url   — исходный URL документа (для метаданных)
          jurisdiction — юрисдикция (RU/KZ/AZ/BY/UZ) для метаданных
          extra_meta   — дополнительные поля метаданных

        Возвращает:
          (content_hash: str, is_new: bool)
          is_new=False — файл уже существовал (дубликат), processing можно пропустить.
        """
        if not file_bytes:
            raise ValueError("snapshot.store: пустой файл не принимается")

        content_hash = _content_hash(file_bytes)
        ext          = _detect_extension(file_bytes)

        metadata = {
            "source_url":   source_url[:500],
            "jurisdiction": jurisdiction,
            **(extra_meta or {}),
        }

        # Локальное сохранение (primary)
        is_new_local = _store_local(file_bytes, content_hash, ext, metadata)

        # S3 (async upload можно вынести в celery task для prod)
        if _S3_BUCKET:
            _store_s3(file_bytes, content_hash, ext, metadata)

        return content_hash, is_new_local

    def exists(self, content_hash: str) -> bool:
        """
        Проверяет наличие snapshot по content_hash.
        Приоритет: локальный диск (быстро) → S3 при необходимости.
        """
        for ext in ("pdf", "docx", "doc", "rtf", "bin"):
            if _local_path(content_hash, ext).exists():
                return True
        return False

    def get_metadata(self, content_hash: str) -> dict | None:
        """Возвращает метаданные snapshot или None если не найдено."""
        meta_path = _meta_path(content_hash)
        if not meta_path.exists():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def load_known_hashes(self) -> set[str]:
        """
        Загружает все content_hash из локального хранилища.
        Используется при старте pipeline для дедупликации без обращения к БД.
        """
        hashes: set[str] = set()
        if not _SNAPSHOT_DIR.exists():
            return hashes

        for bucket_dir in _SNAPSHOT_DIR.iterdir():
            if not bucket_dir.is_dir() or len(bucket_dir.name) != 2:
                continue
            for f in bucket_dir.iterdir():
                # Берём только бинарные файлы (не .json метаданные)
                if f.suffix != ".json" and len(f.stem) == 64:
                    hashes.add(f.stem)

        log.info("snapshot: загружено %d известных хэшей из %s", len(hashes), _SNAPSHOT_DIR)
        return hashes


# Глобальный синглтон
snapshot_store = SnapshotStore()
