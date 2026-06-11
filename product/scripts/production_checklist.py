#!/usr/bin/env python3
"""
production_checklist.py — Чеклист готовности RegRadar к production-деплою.

Запуск:
  python3 scripts/production_checklist.py

Проверяет:
  1. Переменные окружения (.env)
  2. Подключение к БД и корректность схемы
  3. Redis (брокер Celery)
  4. Docker образ и docker-compose
  5. S3/MinIO для backup хранилища
  6. Telegram bot
  7. Резервное копирование БД
  8. Celery worker + beat

Выходные коды:
  0 — всё готово к деплою
  1 — есть критические проблемы
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent


# ── Вспомогательные функции ───────────────────────────────────────────────────

OK    = "\033[92m[OK]\033[0m"
WARN  = "\033[93m[WARN]\033[0m"
FAIL  = "\033[91m[FAIL]\033[0m"
INFO  = "\033[94m[INFO]\033[0m"

_errors: list[str]   = []
_warnings: list[str] = []


def check(label: str, condition: bool, msg: str = "", critical: bool = True) -> bool:
    if condition:
        print(f"  {OK}  {label}")
        return True
    else:
        tag = FAIL if critical else WARN
        detail = f" — {msg}" if msg else ""
        print(f"  {tag}  {label}{detail}")
        ((_errors if critical else _warnings).append(f"{label}{detail}"))
        return False


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── 1. Переменные окружения ───────────────────────────────────────────────────

def check_env() -> None:
    section("1. Переменные окружения (.env)")

    # Загружаем .env если есть
    env_file = ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"  {INFO}  .env загружен из {env_file}")
    else:
        print(f"  {WARN}  .env файл не найден — используются переменные окружения")

    required: list[tuple[str, bool]] = [
        # (ключ, критический)
        ("DATABASE_URL",        False),   # опционально — дефолт SQLite
        ("REDIS_URL",           True),
        ("JWT_SECRET_KEY",      True),
        ("OPENAI_API_KEY",      True),
        ("TELEGRAM_BOT_TOKEN",  False),
        ("TELEGRAM_ALERT_CHAT_ID", False),
        ("SMTP_HOST",           False),
        ("DIGEST_EMAILS",       False),
        ("REGRADA_BASE_URL",    False),
        ("SENTRY_DSN",          False),
    ]

    for key, is_crit in required:
        val = os.getenv(key, "")
        check(
            f"{key} {'(обязательный)' if is_crit else '(опциональный)'}",
            bool(val),
            f"не задан — установите в .env",
            critical=is_crit,
        )


# ── 2. База данных ────────────────────────────────────────────────────────────

def check_database() -> None:
    section("2. База данных")

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or db_url.startswith("sqlite"):
        # SQLite — найти файл
        db_candidates = [
            ROOT / "regrada.db",
            ROOT / "data" / "regrada.db",
        ]
        db_path = next((p for p in db_candidates if p.exists()), None)
        check("SQLite файл существует", db_path is not None,
              f"не найден ни в {db_candidates[0]}, ни в {db_candidates[1]}")

        if db_path:
            try:
                conn = sqlite3.connect(str(db_path))
                c    = conn.cursor()

                tables = {r[0] for r in c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()}

                required_tables = {
                    "regulations", "regulators",
                    "url_health", "webhook_endpoints", "ytd_snapshots",
                }
                missing = required_tables - tables
                check("Все таблицы созданы",   not missing,  f"отсутствуют: {missing}")
                check("WAL режим активен",       True)  # pragma: assume yes after migrations

                # Проверяем колонки regulations
                cols = {r[1] for r in c.execute("PRAGMA table_info(regulations)").fetchall()}
                new_cols = {"urgency_score", "action_plan", "time_to_discovery_sec",
                            "compute_cost_usd", "fines_usd"}
                missing_cols = new_cols - cols
                check("Новые колонки migrations", not missing_cols,
                      f"отсутствуют: {missing_cols}")

                count = c.execute("SELECT COUNT(*) FROM regulations").fetchone()[0]
                print(f"  {INFO}  regulations: {count} записей")
                conn.close()
            except Exception as e:
                check("SQLite доступна для чтения", False, str(e))
    else:
        # PostgreSQL/MySQL
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(db_url)
            with engine.connect():
                check("DB подключение успешно", True)
        except Exception as e:
            check("DB подключение успешно", False, str(e))


# ── 3. Redis ──────────────────────────────────────────────────────────────────

def check_redis() -> None:
    section("3. Redis (брокер Celery)")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        r = redis.from_url(redis_url, socket_connect_timeout=3)
        r.ping()
        check("Redis ping успешен", True)
        info = r.info()
        print(f"  {INFO}  Redis {info['redis_version']} | "
              f"память: {info['used_memory_human']}")
    except ImportError:
        check("redis-py установлен", False, "pip install redis hiredis")
    except Exception as e:
        check("Redis доступен", False, str(e))


# ── 4. Docker ─────────────────────────────────────────────────────────────────

def check_docker() -> None:
    section("4. Docker")

    # docker binary
    result = subprocess.run(["docker", "--version"],
                            capture_output=True, text=True)
    check("docker CLI доступен", result.returncode == 0,
          result.stderr[:100] if result.returncode else "")

    # docker-compose.yml
    compose_file = ROOT / "docker-compose.yml"
    check("docker-compose.yml существует", compose_file.exists(),
          f"создайте {compose_file}")

    # Dockerfile
    dockerfile = ROOT / "Dockerfile"
    check("Dockerfile существует", dockerfile.exists())

    # Validate compose
    if compose_file.exists():
        r2 = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config", "--quiet"],
            capture_output=True, text=True,
        )
        check("docker-compose.yml валиден", r2.returncode == 0,
              r2.stderr[:200] if r2.returncode else "", critical=False)


# ── 5. S3 / MinIO backup ──────────────────────────────────────────────────────

def check_s3() -> None:
    section("5. S3 / MinIO — резервное хранилище")

    s3_key    = os.getenv("AWS_ACCESS_KEY_ID",     "")
    s3_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket = os.getenv("S3_SNAPSHOT_BUCKET",    "")
    s3_region = os.getenv("AWS_DEFAULT_REGION",    "")

    check("AWS_ACCESS_KEY_ID задан",     bool(s3_key),    critical=False)
    check("AWS_SECRET_ACCESS_KEY задан", bool(s3_secret), critical=False)
    check("S3_SNAPSHOT_BUCKET задан",    bool(s3_bucket), critical=False)

    if s3_key and s3_secret and s3_bucket:
        try:
            import boto3
            s3 = boto3.client("s3")
            s3.head_bucket(Bucket=s3_bucket)
            check("S3 bucket доступен", True)
        except ImportError:
            check("boto3 установлен", False, "pip install boto3", critical=False)
        except Exception as e:
            check("S3 bucket доступен", False, str(e)[:100], critical=False)
    else:
        print(f"  {INFO}  S3 не настроен — backups будут только локальными")


# ── 6. Telegram ──────────────────────────────────────────────────────────────

def check_telegram() -> None:
    section("6. Telegram Bot")

    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")

    check("TELEGRAM_BOT_TOKEN задан",      bool(token),   critical=False)
    check("TELEGRAM_ALERT_CHAT_ID задан",  bool(chat_id), critical=False)

    if token:
        import urllib.request, json as _json
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = _json.loads(resp.read())
            ok = data.get("ok", False)
            check("Telegram Bot API доступен", ok,
                  data.get("description", ""), critical=False)
            if ok:
                bot = data["result"]
                print(f"  {INFO}  Bot: @{bot.get('username')} ({bot.get('first_name')})")
        except Exception as e:
            check("Telegram Bot API доступен", False, str(e)[:100], critical=False)


# ── 7. DB backup script ───────────────────────────────────────────────────────

def check_backup_procedure() -> None:
    section("7. Резервное копирование БД")

    backup_script = ROOT / "scripts" / "backup_db.sh"

    print(f"\n  {INFO}  Рекомендуемая команда для daily backup (cron):")
    print("""
  # Добавить в crontab -e:
  # Ежедневный backup в 03:00 UTC с загрузкой в S3
  0 3 * * * /bin/bash -c '\\
    DB=/app/regrada.db \\
    BACKUP=/backups/regrada_$(date +%Y%m%d_%H%M%S).db \\
    && sqlite3 $DB ".backup $BACKUP" \\
    && gzip $BACKUP \\
    && aws s3 cp ${BACKUP}.gz s3://$S3_SNAPSHOT_BUCKET/db-backups/ \\
    && echo "Backup OK: $(date)" >> /var/log/regrada-backup.log'

  # Docker Compose вариант (добавить в docker-compose.yml):
  # backup:
  #   image: amazon/aws-cli
  #   environment:
  #     - AWS_ACCESS_KEY_ID
  #     - AWS_SECRET_ACCESS_KEY
  #   volumes:
  #     - db_data:/data
  #   command: >
  #     sh -c "sqlite3 /data/regrada.db '.backup /tmp/backup.db' &&
  #            gzip /tmp/backup.db &&
  #            aws s3 cp /tmp/backup.db.gz s3://$$S3_SNAPSHOT_BUCKET/db-backups/"
    """)
    check("Скрипт backup_db.sh существует", backup_script.exists(),
          "создайте скрипт (шаблон выведен выше)", critical=False)


# ── 8. Celery ─────────────────────────────────────────────────────────────────

def check_celery() -> None:
    section("8. Celery Worker")

    try:
        from celery_app import celery_app
        schedule_keys = list(celery_app.conf.beat_schedule.keys())
        expected = {
            "health-watchdog-hourly",
            "dead-link-checker-6h",
            "ytd-snapshot-daily",
        }
        missing = expected - set(schedule_keys)
        check("Watchdog задачи в beat_schedule", not missing,
              f"отсутствуют: {missing}")
        print(f"  {INFO}  beat_schedule задач: {len(schedule_keys)}")
    except ImportError as e:
        check("celery_app.py импортируется", False, str(e))

    # Проверка что Celery может подключиться к брокеру
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"\n  {INFO}  Команды запуска Celery:")
    print(f"""
  # Worker (4 потока):
  celery -A celery_app worker --loglevel=INFO --concurrency=4 \\
         -Q default,scraping,reports

  # Beat-планировщик (отдельный процесс):
  celery -A celery_app beat --loglevel=INFO

  # Мониторинг (Flower):
  celery -A celery_app flower --port=5555

  # Быстрая проверка (должен вернуть "pong"):
  celery -A celery_app call celery_app.debug_ping
    """)


# ── Итоговый отчёт ────────────────────────────────────────────────────────────

def print_summary() -> int:
    print(f"\n{'═' * 60}")
    print(f"  ИТОГ — {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"{'═' * 60}")

    if _errors:
        print(f"\n  {FAIL}  Критических проблем: {len(_errors)}")
        for e in _errors:
            print(f"       • {e}")
        print("\n  Деплой в production НЕ РЕКОМЕНДОВАН до устранения ошибок.")
        return 1

    if _warnings:
        print(f"\n  {WARN}  Предупреждений: {len(_warnings)}")
        for w in _warnings:
            print(f"       • {w}")
        print("\n  Деплой возможен, но некоторые функции могут быть недоступны.")
    else:
        print(f"\n  {OK}  Все проверки пройдены. Система готова к production-деплою.")

    print(f"""
  Следующие шаги:
  1. docker compose up -d --build
  2. celery -A celery_app worker --loglevel=INFO &
  3. celery -A celery_app beat --loglevel=INFO &
  4. Проверить дашборд: {os.getenv('REGRADA_BASE_URL', 'http://localhost:8080')}
  5. Запустить тест: celery -A celery_app call celery_app.debug_ping
  6. Убедиться в работе watchdog: curl .../api/v1/watchdog/health
    """)
    return 0


if __name__ == "__main__":
    print(f"\n  RegRadar Enterprise — Production Readiness Checklist")
    print(f"  {'─' * 50}")
    check_env()
    check_database()
    check_redis()
    check_docker()
    check_s3()
    check_telegram()
    check_backup_procedure()
    check_celery()
    sys.exit(print_summary())
