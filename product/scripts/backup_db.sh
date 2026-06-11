#!/usr/bin/env bash
# =============================================================================
# scripts/backup_db.sh — RegRadar Enterprise: Автоматизированное резервное копирование
# =============================================================================
#
# Назначение:
#   Горячее WAL-безопасное резервное копирование SQLite через
#   sqlite3.Connection.backup(), вычисление SHA-256 хэша целостности,
#   сжатие в .tar.gz с временной меткой, применение политики хранения
#   и опциональная выгрузка в S3-совместимое хранилище.
#
# Запуск внутри Docker-контейнера (рекомендуемый способ):
#   docker compose exec -T web-api bash /app/scripts/backup_db.sh
#   docker compose exec -T web-api bash /app/scripts/backup_db.sh --dry-run
#   docker compose exec -T web-api bash /app/scripts/backup_db.sh --no-s3
#
# Запуск вне Docker (для тестирования — переопределяем пути через env):
#   REGRADA_DB_PATH=./data/regrada.db REGRADA_BACKUP_DIR=./backups bash scripts/backup_db.sh
#
# Cron на хост-машине (ежедневно в 03:00):
#   0 3 * * * docker compose -f /opt/regrada/docker-compose.yml exec -T web-api \
#             bash /app/scripts/backup_db.sh >> /var/log/regrada_backup.log 2>&1
#
# Переменные окружения:
#   REGRADA_DB_PATH         — путь к regrada.db (умолч. /app/data/regrada.db)
#   REGRADA_BACKUP_DIR      — директория резервных копий (умолч. /app/backups)
#   BACKUP_RETENTION_DAYS   — хранить копии N дней (умолч. 30)
#   S3_BUCKET               — имя S3/MinIO бакета (пусто = S3 пропускается)
#   S3_ENDPOINT             — кастомный endpoint MinIO (напр. http://minio:9000)
#   S3_ACCESS_KEY           — ключ доступа S3/MinIO
#   S3_SECRET_KEY           — секретный ключ S3/MinIO
#   S3_REGION               — регион S3 (умолч. us-east-1)
#   S3_PREFIX               — папка внутри бакета (умолч. regrada/backups)
#
# Коды выхода:
#   0 — резервная копия создана успешно
#   1 — ошибка (БД не найдена, Python упал, SHA-256 не совпал, и т.д.)
# =============================================================================

set -euo pipefail

readonly SCRIPT_VERSION="1.1.0"

# =============================================================================
# ДИНАМИЧЕСКИЕ ПУТИ (переопределяются через переменные окружения)
# =============================================================================

# DB_PATH и BACKUP_DIR намеренно НЕ объявлены через readonly —
# они должны быть перезаписываемы при тестировании вне Docker-окружения.
#
# Логика разрешения пути (в порядке приоритета):
#   1. Переменная окружения REGRADA_DB_PATH / REGRADA_BACKUP_DIR (задана явно)
#   2. Значение по умолчанию — абсолютный путь Docker volume mount-point
#
# Такой подход позволяет запускать скрипт и внутри контейнера (production),
# и напрямую с хоста (тестирование), без изменения кода.
DB_PATH="${REGRADA_DB_PATH:-/app/data/regrada.db}"
BACKUP_DIR="${REGRADA_BACKUP_DIR:-/app/backups}"

readonly LOG_TAG="[RegRadar Backup]"

# Временная директория для промежуточных файлов.
# Инициализируется пустой строкой; заполняется через mktemp в теле скрипта.
# Обработчик EXIT гарантирует её удаление при любом завершении скрипта.
TEMP_DIR=""

# =============================================================================
# ЦВЕТА И ФОРМАТИРОВАНИЕ ВЫВОДА
# =============================================================================

# ANSI escape-коды включаем только если stdout подключён к терминалу.
# В cron / pipe / docker exec -T цвета не нужны и могут засорить лог-файл.
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
fi

# Вспомогательные функции логирования с временной меткой
log_info()    { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ${LOG_TAG} INFO:${NC}  $*"; }
log_warn()    { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ${LOG_TAG} WARN:${NC}  $*" >&2; }
log_error()   { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ${LOG_TAG} ERROR:${NC} $*" >&2; }
log_ok()      { echo -e "${GREEN}  ✔ $*${NC}"; }
log_step()    { echo -e "${CYAN}  ▶ $*${NC}"; }
log_section() {
    echo -e "\n${BLUE}${BOLD}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $*${NC}"
    echo -e "${BLUE}${BOLD}════════════════════════════════════════════${NC}"
}


# =============================================================================
# ОБРАБОТЧИК ЗАВЕРШЕНИЯ (trap)
# =============================================================================

# Функция cleanup вызывается при ЛЮБОМ выходе из скрипта:
# нормальном завершении, ошибке (set -e), сигналах INT/TERM.
# Это гарантирует что временные файлы всегда будут удалены,
# даже если скрипт прервётся на середине.
cleanup() {
    local _exit_code=$?

    if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
        log_step "Временная директория удалена: ${TEMP_DIR}"
    fi

    if [[ ${_exit_code} -ne 0 ]]; then
        log_error "Резервное копирование завершилось с ошибкой. Код выхода: ${_exit_code}"
    fi

    exit "${_exit_code}"
}

trap cleanup EXIT INT TERM


# =============================================================================
# РАЗБОР АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ
# =============================================================================

DRY_RUN=false   # --dry-run: симуляция без записи файлов
SKIP_S3=false   # --no-s3:   пропустить выгрузку в S3/MinIO

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            log_warn "Режим DRY-RUN активирован — файлы не будут записаны или отправлены"
            shift ;;
        --no-s3)
            SKIP_S3=true
            log_info "Выгрузка в S3 отключена флагом --no-s3"
            shift ;;
        --help|-h)
            echo ""
            echo "Использование: $0 [--dry-run] [--no-s3] [--help]"
            echo ""
            echo "  --dry-run   Симуляция: показывает что будет сделано, ничего не пишет"
            echo "  --no-s3     Пропустить выгрузку архива в S3/MinIO"
            echo "  --help      Показать эту справку"
            echo ""
            echo "Переопределение путей через env:"
            echo "  REGRADA_DB_PATH=./local.db REGRADA_BACKUP_DIR=./bak $0"
            echo ""
            exit 0 ;;
        *)
            log_error "Неизвестный аргумент: '$1'. Запустите '$0 --help'."
            exit 1 ;;
    esac
done


# =============================================================================
# ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# =============================================================================

# Внутри Docker-контейнера все переменные уже переданы через env_file
# директиву docker-compose.yml. Загрузка /app/.env нужна только при прямом
# запуске скрипта вне compose-окружения (например, для тестирования на хосте).
if [[ -f "/app/.env" ]]; then
    set +euo pipefail
    # shellcheck disable=SC1091
    source <(
        grep -v '^\s*#' "/app/.env" \
        | grep -v '^\s*$' \
        | sed 's/^/export /'
    ) 2>/dev/null || true
    set -euo pipefail
fi

# Настройки резервного копирования из окружения (с безопасными умолчаниями)
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
S3_ENDPOINT="${S3_ENDPOINT:-}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-}"
S3_SECRET_KEY="${S3_SECRET_KEY:-}"
S3_REGION="${S3_REGION:-us-east-1}"
S3_PREFIX="${S3_PREFIX:-regrada/backups}"

# После загрузки .env пути могут быть перезаписаны переменными окружения.
# Применяем снова для случая когда REGRADA_DB_PATH задан в .env:
DB_PATH="${REGRADA_DB_PATH:-${DB_PATH}}"
BACKUP_DIR="${REGRADA_BACKUP_DIR:-${BACKUP_DIR}}"


# =============================================================================
# МЕТКА ВРЕМЕНИ И ИМЕНА ФАЙЛОВ
# =============================================================================

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
BACKUP_STEM="regrada_${TIMESTAMP}"

# Промежуточный файл .db (горячая копия SQLite во временной директории)
BACKUP_SQL="${BACKUP_STEM}.db"

# Финальный сжатый архив (содержит .db + .sha256)
BACKUP_ARCHIVE="${BACKUP_STEM}.tar.gz"

# Файл SHA-256 контрольной суммы (хранится отдельно для быстрой проверки)
CHECKSUM_FILE="${BACKUP_STEM}.sha256"


# =============================================================================
# ШАГ 1: ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ
# =============================================================================

log_section "RegRadar Backup v${SCRIPT_VERSION} | ${TIMESTAMP}"
log_info "Источник БД:    ${DB_PATH}"
log_info "Директория:     ${BACKUP_DIR}"
log_info "Retention:      ${BACKUP_RETENTION_DAYS} дней"
log_info "S3 бакет:       ${S3_BUCKET:-не задан}"
log_info "DRY-RUN:        ${DRY_RUN}"

log_section "Шаг 1: Предварительные проверки"

# Python 3 обязателен: используется для WAL-backup, SHA-256 и S3-выгрузки
if ! command -v python3 &>/dev/null; then
    log_error "python3 не найден в PATH. Скрипт требует Python 3.8+."
    exit 1
fi
log_ok "Python 3: $(python3 --version)"

# Проверяем существование исходной базы данных.
# Если БД не существует — значит приложение ещё ни разу не запускалось.
if [[ ! -f "${DB_PATH}" ]]; then
    log_error "База данных не найдена: ${DB_PATH}"
    log_error "Убедитесь что:"
    log_error "  1. Приложение было запущено хотя бы один раз (инициализация схемы)"
    log_error "  2. Переменная REGRADA_DB_PATH указывает на корректный путь"
    log_error "  3. Docker volume db_data смонтирован в /app/data/"
    exit 1
fi

# Получаем размер БД (кросс-платформенно: Linux stat -c, macOS stat -f)
DB_SIZE_BYTES=$(
    stat -c%s "${DB_PATH}" 2>/dev/null \
    || stat -f%z "${DB_PATH}" 2>/dev/null \
    || echo "0"
)

# Форматируем размер в человекочитаемый вид через Python
DB_SIZE_HUMAN=$(python3 -c "
size = ${DB_SIZE_BYTES}
for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
    if size < 1024.0:
        print(f'{size:.1f} {unit}')
        break
    size /= 1024.0
")
log_ok "База данных: ${DB_PATH} (${DB_SIZE_HUMAN})"

# Создаём директорию резервных копий если не существует
if [[ ! -d "${BACKUP_DIR}" ]]; then
    if [[ "${DRY_RUN}" == "false" ]]; then
        mkdir -p "${BACKUP_DIR}"
        log_ok "Директория резервных копий создана: ${BACKUP_DIR}"
    else
        log_info "[DRY-RUN] mkdir -p ${BACKUP_DIR}"
    fi
else
    log_ok "Директория резервных копий существует: ${BACKUP_DIR}"
fi

# Проверяем достаточность свободного места.
# Требуем минимум 3× размер БД: 1× для .db-копии + 1× для .tar.gz + буфер.
REQUIRED_BYTES=$(( DB_SIZE_BYTES * 3 ))
AVAIL_BYTES=$(
    df -B1 "${BACKUP_DIR}" 2>/dev/null | awk 'NR==2{print $4}' \
    || echo "999999999999"
)
if [[ "${AVAIL_BYTES}" -lt "${REQUIRED_BYTES}" ]]; then
    log_error "Недостаточно свободного места в ${BACKUP_DIR}:"
    log_error "  Требуется: ~$(( REQUIRED_BYTES / 1024 / 1024 )) МБ"
    log_error "  Доступно:  ~$(( AVAIL_BYTES  / 1024 / 1024 )) МБ"
    log_error "Освободите место или уменьшите BACKUP_RETENTION_DAYS."
    exit 1
fi
log_ok "Свободного места достаточно (~$(( AVAIL_BYTES / 1024 / 1024 )) МБ доступно)"


# =============================================================================
# ШАГ 2: WAL-БЕЗОПАСНОЕ ГОРЯЧЕЕ РЕЗЕРВНОЕ КОПИРОВАНИЕ
# =============================================================================

log_section "Шаг 2: Горячее резервное копирование SQLite (WAL-safe)"

# Создаём изолированную временную директорию.
# mktemp -d создаёт директорию с уникальным именем в /tmp.
# trap cleanup гарантирует её удаление при выходе (даже при ошибке).
TEMP_DIR="$(mktemp -d /tmp/regrada_backup_XXXXXX)"
TEMP_BACKUP="${TEMP_DIR}/${BACKUP_SQL}"

log_step "Источник:  ${DB_PATH}"
log_step "Временный: ${TEMP_BACKUP}"

if [[ "${DRY_RUN}" == "false" ]]; then
    # ПОЧЕМУ sqlite3.Connection.backup() а не cp/rsync:
    #
    # SQLite с WAL (Write-Ahead Logging) хранит незакоммиченные транзакции
    # в отдельном .wal файле. Простое копирование .db файла в момент активной
    # записи даст НЕСОГЛАСОВАННУЮ копию (частично применённые транзакции).
    #
    # sqlite3.Connection.backup() — официальный Python API для онлайн-бэкапа.
    # Он использует SQLite Online Backup API (sqlite3_backup_*) который:
    #   - Корректно объединяет .db + .wal в единый согласованный снэпшот
    #   - Работает без блокировки читателей (только кратковременная read lock)
    #   - Поддерживает pages=-1 (копирует всё за один проход)
    #   - Поддерживает progress-колбэк для мониторинга крупных БД
    #
    # Передаём пути через переменные окружения (_REGRADA_SRC, _REGRADA_DST)
    # потому что heredoc с одинарными кавычками ('PYEOF') не интерполирует
    # bash-переменные — это намеренно для безопасности (нет shell injection).
    _REGRADA_SRC="${DB_PATH}" \
    _REGRADA_DST="${TEMP_BACKUP}" \
    python3 - <<'PYEOF'
import sqlite3
import sys
import os

src_path = os.environ["_REGRADA_SRC"]
dst_path = os.environ["_REGRADA_DST"]

def _progress(status, remaining, total):
    """Колбэк прогресса: вызывается SQLite после каждой скопированной страницы."""
    if total > 0 and remaining % 200 == 0 and remaining != total:
        copied = total - remaining
        pct = int(copied / total * 100)
        print(f"  • Прогресс: {pct}% ({copied}/{total} страниц)", flush=True)

try:
    # Открываем оба соединения в режиме без автоматического commit.
    # src: соединение к живой БД (read-only семантика для backup)
    # dst: соединение к новому пустому файлу (будет заполнен backup-ом)
    with sqlite3.connect(src_path) as src, sqlite3.connect(dst_path) as dst:
        # pages=-1: копируем все страницы за один вызов (нет итеративного прогресса)
        # progress: колбэк для отображения процента выполнения
        src.backup(dst, pages=-1, progress=_progress)

    # Проверяем что файл создан и не пустой
    size = os.path.getsize(dst_path)
    if size == 0:
        print("[ОШИБКА] WAL-копия создана, но файл пустой!", file=sys.stderr)
        sys.exit(1)

    print(f"  ✔ WAL-копия создана успешно: {size:,} байт", flush=True)
    sys.exit(0)

except sqlite3.Error as e:
    print(f"[ОШИБКА] SQLite backup API: {e}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"[ОШИБКА] Файловая система: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ОШИБКА] Неожиданная ошибка: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    log_ok "SQLite WAL-backup завершён: ${TEMP_BACKUP}"
else
    log_info "[DRY-RUN] sqlite3.connect('${DB_PATH}').backup(dst) → ${TEMP_BACKUP}"
fi


# =============================================================================
# ШАГ 3: ВЫЧИСЛЕНИЕ SHA-256 КОНТРОЛЬНОЙ СУММЫ
# =============================================================================

log_section "Шаг 3: Вычисление SHA-256 контрольной суммы"

TEMP_CHECKSUM="${TEMP_DIR}/${CHECKSUM_FILE}"

if [[ "${DRY_RUN}" == "false" ]]; then
    # Используем Python hashlib вместо sha256sum / shasum для кросс-платформенности.
    # sha256sum есть в Linux но отсутствует в macOS по умолчанию (там shasum -a 256).
    # Python hashlib работает одинаково на всех платформах.
    # Читаем файл блоками по 64 КБ чтобы не загружать всю БД в оперативную память.
    SHA256=$(
        _REGRADA_FILE="${TEMP_BACKUP}" python3 -c "
import hashlib, os, sys
path = os.environ['_REGRADA_FILE']
h = hashlib.sha256()
try:
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    print(h.hexdigest())
except OSError as e:
    print(f'[ОШИБКА] {e}', file=sys.stderr)
    sys.exit(1)
"
    )

    # Формат файла совместим со стандартным sha256sum:
    # "<hex-хэш>  <имя-файла>" (два пробела — стандарт)
    echo "${SHA256}  ${BACKUP_SQL}" > "${TEMP_CHECKSUM}"

    log_ok "SHA-256: ${SHA256}"
    log_ok "Checksum файл: ${TEMP_CHECKSUM}"
else
    SHA256="<sha256-dry-run-placeholder>"
    log_info "[DRY-RUN] SHA-256 вычисление пропущено"
fi


# =============================================================================
# ШАГ 4: СЖАТИЕ В tar.gz АРХИВ
# =============================================================================

log_section "Шаг 4: Сжатие резервной копии в .tar.gz"

TEMP_ARCHIVE="${TEMP_DIR}/${BACKUP_ARCHIVE}"

# Финальные пути (в директории резервных копий)
FINAL_ARCHIVE="${BACKUP_DIR}/${BACKUP_ARCHIVE}"
FINAL_CHECKSUM="${BACKUP_DIR}/${CHECKSUM_FILE}"

log_step "Архив: ${FINAL_ARCHIVE}"

if [[ "${DRY_RUN}" == "false" ]]; then
    # tar флаги:
    #   -c: создать архив
    #   -z: сжать через gzip
    #   -f: имя файла архива
    #   -C: смена рабочей директории перед добавлением файлов
    # Использование -C "${TEMP_DIR}" гарантирует что в архиве хранятся
    # ОТНОСИТЕЛЬНЫЕ пути (regrada_20260520_030000.db), а не абсолютные
    # (/tmp/regrada_backup_XXXXX/regrada_20260520_030000.db).
    # Это важно для переносимости: архив можно распаковать в любой директории.
    tar -czf "${TEMP_ARCHIVE}" \
        -C "${TEMP_DIR}" \
        "${BACKUP_SQL}" \
        "${CHECKSUM_FILE}"

    # Получаем размер архива для отображения коэффициента сжатия
    ARCHIVE_SIZE_BYTES=$(
        stat -c%s "${TEMP_ARCHIVE}" 2>/dev/null \
        || stat -f%z "${TEMP_ARCHIVE}" 2>/dev/null \
        || echo "0"
    )

    # Форматируем и вычисляем коэффициент сжатия через Python
    python3 - <<PYEOF_STATS
orig = ${DB_SIZE_BYTES}
comp = ${ARCHIVE_SIZE_BYTES}
for size, label in [(comp, 'Архив'), (orig, 'Оригинал')]:
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            print(f"  {label}: {size:.1f} {unit}", flush=True)
            break
        size /= 1024.0
ratio = (1 - comp / orig) * 100 if orig > 0 else 0
print(f"  Сжатие:  {ratio:.1f}%", flush=True)
PYEOF_STATS

    # Атомарно перемещаем готовые файлы из /tmp в BACKUP_DIR.
    # mv атомарен в пределах одной файловой системы: нет частичных файлов
    # если скрипт прервётся между шагами.
    mv "${TEMP_ARCHIVE}"   "${FINAL_ARCHIVE}"
    mv "${TEMP_CHECKSUM}"  "${FINAL_CHECKSUM}"

    log_ok "Архив перемещён в: ${BACKUP_DIR}"
else
    log_info "[DRY-RUN] tar -czf ${TEMP_ARCHIVE} -C ${TEMP_DIR} ${BACKUP_SQL} ${CHECKSUM_FILE}"
    log_info "[DRY-RUN] mv → ${FINAL_ARCHIVE}"
    log_info "[DRY-RUN] mv → ${FINAL_CHECKSUM}"
fi


# =============================================================================
# ШАГ 5: ПРОВЕРКА ЦЕЛОСТНОСТИ АРХИВА
# =============================================================================

log_section "Шаг 5: Верификация целостности архива"

if [[ "${DRY_RUN}" == "false" ]]; then
    # Извлекаем архив во временную директорию и пересчитываем SHA-256.
    # Это подтверждает что:
    #   1. tar-архив не повреждён и успешно распаковывается
    #   2. Содержимое .db файла совпадает с тем что мы хэшировали в шаге 3
    #   3. Никаких побитовых ошибок при сжатии/распаковке не произошло
    VERIFY_DIR="$(mktemp -d /tmp/regrada_verify_XXXXXX)"

    # Распаковываем архив в директорию верификации
    tar -xzf "${FINAL_ARCHIVE}" -C "${VERIFY_DIR}" 2>/dev/null

    # Пересчитываем SHA-256 извлечённого файла
    VERIFY_HASH=$(
        _REGRADA_FILE="${VERIFY_DIR}/${BACKUP_SQL}" python3 -c "
import hashlib, os, sys
path = os.environ['_REGRADA_FILE']
h = hashlib.sha256()
try:
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    print(h.hexdigest())
except OSError as e:
    print(f'[ОШИБКА] {e}', file=sys.stderr)
    sys.exit(1)
"
    )

    # Удаляем директорию верификации немедленно (не ждём trap cleanup)
    rm -rf "${VERIFY_DIR}"

    if [[ "${VERIFY_HASH}" == "${SHA256}" ]]; then
        log_ok "Контрольная сумма подтверждена — архив целостен"
        log_step "  SHA-256: ${VERIFY_HASH}"
    else
        log_error "КРИТИЧЕСКАЯ ОШИБКА: контрольная сумма НЕ совпадает!"
        log_error "  Ожидалось: ${SHA256}"
        log_error "  Получено:  ${VERIFY_HASH}"
        log_error "Архив повреждён. Удаляем некорректные файлы."
        rm -f "${FINAL_ARCHIVE}" "${FINAL_CHECKSUM}"
        exit 1
    fi
else
    log_info "[DRY-RUN] Верификация архива пропущена"
fi


# =============================================================================
# ШАГ 6: ВЫГРУЗКА В S3/MinIO (опционально)
# =============================================================================

log_section "Шаг 6: Выгрузка в S3/MinIO"

if [[ "${SKIP_S3}" == "true" ]]; then
    log_info "Выгрузка в S3 пропущена (флаг --no-s3)"
elif [[ -z "${S3_BUCKET}" ]]; then
    log_info "S3_BUCKET не задан — выгрузка в S3 пропущена"
    log_info "Для включения S3 задайте S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY в .env"
else
    log_step "Бакет:     ${S3_BUCKET}"
    log_step "Префикс:   ${S3_PREFIX}"
    log_step "Endpoint:  ${S3_ENDPOINT:-aws-default (us-east-1)}"
    log_step "Регион:    ${S3_REGION}"

    if [[ "${DRY_RUN}" == "false" ]]; then
        # Выгружаем архив и файл контрольной суммы через boto3.
        # Передаём все параметры через переменные окружения — не через
        # аргументы командной строки, чтобы секреты не попали в ps aux.
        _S3_BUCKET="${S3_BUCKET}" \
        _S3_ENDPOINT="${S3_ENDPOINT}" \
        _S3_ACCESS_KEY="${S3_ACCESS_KEY}" \
        _S3_SECRET_KEY="${S3_SECRET_KEY}" \
        _S3_REGION="${S3_REGION}" \
        _S3_PREFIX="${S3_PREFIX}" \
        _S3_ARCHIVE_PATH="${FINAL_ARCHIVE}" \
        _S3_CHECKSUM_PATH="${FINAL_CHECKSUM}" \
        _S3_ARCHIVE_NAME="${BACKUP_ARCHIVE}" \
        _S3_CHECKSUM_NAME="${CHECKSUM_FILE}" \
        python3 - <<'PYEOF_S3'
import sys
import os

# Читаем параметры из переменных окружения
bucket        = os.environ["_S3_BUCKET"]
endpoint      = os.environ.get("_S3_ENDPOINT") or None
access_key    = os.environ.get("_S3_ACCESS_KEY") or None
secret_key    = os.environ.get("_S3_SECRET_KEY") or None
region        = os.environ.get("_S3_REGION", "us-east-1")
prefix        = os.environ.get("_S3_PREFIX", "regrada/backups").rstrip("/")
archive_path  = os.environ["_S3_ARCHIVE_PATH"]
checksum_path = os.environ["_S3_CHECKSUM_PATH"]
archive_name  = os.environ["_S3_ARCHIVE_NAME"]
checksum_name = os.environ["_S3_CHECKSUM_NAME"]

# boto3 может отсутствовать в контейнере если не добавлен в requirements.txt.
# Это не фатальная ошибка — локальная копия уже создана и верифицирована.
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    print("  [ПРЕДУПРЕЖДЕНИЕ] boto3 не установлен — S3-выгрузка невозможна", file=sys.stderr)
    print("  Локальная резервная копия сохранена успешно.", file=sys.stderr)
    print("  Для включения S3: добавьте boto3 в requirements.txt", file=sys.stderr)
    sys.exit(0)  # Не фатально — только локальное резервное копирование

# Настраиваем boto3 клиент.
# endpoint_url: для MinIO или других S3-совместимых хранилищ (Yandex Object Storage и т.д.)
# Если None — используется стандартный AWS S3 endpoint.
client_kwargs = {
    "region_name":           region,
    "aws_access_key_id":     access_key,
    "aws_secret_access_key": secret_key,
}
if endpoint:
    client_kwargs["endpoint_url"] = endpoint

try:
    s3 = boto3.client("s3", **client_kwargs)

    # Выгружаем оба файла: архив и файл контрольной суммы
    upload_pairs = [
        (archive_path,  archive_name),
        (checksum_path, checksum_name),
    ]

    for local_path, remote_name in upload_pairs:
        s3_key  = f"{prefix}/{remote_name}"
        file_sz = os.path.getsize(local_path)

        print(f"  ▶ Выгрузка: s3://{bucket}/{s3_key} ({file_sz:,} байт)", flush=True)

        s3.upload_file(
            local_path,
            bucket,
            s3_key,
            ExtraArgs={
                # Серверное шифрование: AES-256 (SSE-S3)
                # Защищает данные БД в хранилище (GDPR/PCI DSS требование)
                "ServerSideEncryption": "AES256",
                # Метаданные для идентификации источника
                "Metadata": {
                    "source":    "regrada-enterprise",
                    "timestamp": os.path.basename(local_path).split("_", 1)[1].split(".")[0]
                                 if "_" in os.path.basename(local_path) else "unknown",
                },
            },
        )

        print(f"  ✔ Выгружено: s3://{bucket}/{s3_key}", flush=True)

    print(f"\n  Все файлы выгружены в s3://{bucket}/{prefix}/", flush=True)

except (BotoCoreError, ClientError) as e:
    print(f"[ОШИБКА] S3/boto3: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ОШИБКА] Неожиданная ошибка при S3-выгрузке: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF_S3

        log_ok "S3-выгрузка завершена: s3://${S3_BUCKET}/${S3_PREFIX}/"
    else
        log_info "[DRY-RUN] s3.upload_file(${BACKUP_ARCHIVE}) → s3://${S3_BUCKET}/${S3_PREFIX}/"
        log_info "[DRY-RUN] s3.upload_file(${CHECKSUM_FILE}) → s3://${S3_BUCKET}/${S3_PREFIX}/"
    fi
fi


# =============================================================================
# ШАГ 7: УДАЛЕНИЕ УСТАРЕВШИХ РЕЗЕРВНЫХ КОПИЙ (RETENTION POLICY)
# =============================================================================

log_section "Шаг 7: Применение политики хранения (retention)"
log_step "Порог: удалять копии старше ${BACKUP_RETENTION_DAYS} дней"

if [[ "${DRY_RUN}" == "false" ]]; then
    DELETED_COUNT=0
    DELETED_SIZE_BYTES=0

    # find с -print0 и read -d '' безопасно обрабатывают имена файлов
    # с пробелами, переносами строк и спецсимволами.
    # -maxdepth 1: не рекурсируем в поддиректории
    # -mtime +N:   файлы изменённые более N дней назад
    while IFS= read -r -d '' old_archive; do
        _fsz=$(
            stat -c%s "${old_archive}" 2>/dev/null \
            || stat -f%z "${old_archive}" 2>/dev/null \
            || echo "0"
        )
        log_step "Удаление: ${old_archive} ($( echo "${_fsz}" | awk '{printf "%.1f КБ", $1/1024}' ))"
        rm -f "${old_archive}"

        # Удаляем связанный .sha256 файл если существует
        _old_checksum="${old_archive%.tar.gz}.sha256"
        if [[ -f "${_old_checksum}" ]]; then
            rm -f "${_old_checksum}"
            log_step "Удалён checksum: ${_old_checksum}"
        fi

        DELETED_COUNT=$(( DELETED_COUNT + 1 ))
        DELETED_SIZE_BYTES=$(( DELETED_SIZE_BYTES + _fsz ))
    done < <(
        find "${BACKUP_DIR}" \
            -maxdepth 1 \
            -name "regrada_*.tar.gz" \
            -mtime "+${BACKUP_RETENTION_DAYS}" \
            -print0 \
            2>/dev/null
    )

    if [[ "${DELETED_COUNT}" -gt 0 ]]; then
        FREED_HUMAN=$(python3 -c "
size = ${DELETED_SIZE_BYTES}
for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
    if size < 1024.0:
        print(f'{size:.1f} {unit}')
        break
    size /= 1024.0
")
        log_ok "Удалено устаревших копий: ${DELETED_COUNT} (освобождено ${FREED_HUMAN})"
    else
        log_ok "Устаревших копий не найдено (retention: ${BACKUP_RETENTION_DAYS} дней)"
    fi

    # Показываем текущий список резервных копий в директории
    echo ""
    log_info "Текущие резервные копии в ${BACKUP_DIR}:"

    # -printf доступен в GNU find (Linux); на macOS используем ls как fallback
    if find "${BACKUP_DIR}" -maxdepth 1 -name "regrada_*.tar.gz" \
            -printf "  %TY-%Tm-%Td %TH:%TM  %f\n" 2>/dev/null | sort -r | head -10; then
        : # GNU find сработал
    else
        ls -lht "${BACKUP_DIR}"/regrada_*.tar.gz 2>/dev/null \
            | awk '{printf "  %s %s  %s\n", $6, $7, $9}' \
            | head -10 \
            || log_info "  (нет резервных копий в ${BACKUP_DIR})"
    fi
else
    log_info "[DRY-RUN] find ${BACKUP_DIR} -mtime +${BACKUP_RETENTION_DAYS} -name 'regrada_*.tar.gz'"
    log_info "[DRY-RUN] Удаление устаревших файлов пропущено"
fi


# =============================================================================
# ИТОГОВЫЙ ОТЧЁТ
# =============================================================================

log_section "Резервное копирование завершено успешно"

if [[ "${DRY_RUN}" == "false" ]]; then
    echo -e "${GREEN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║           RegRadar Backup — ЗАВЕРШЕНО УСПЕШНО ✓             ║"
    echo "  ╠══════════════════════════════════════════════════════════════╣"
    echo "  ║                                                              ║"
    printf "  ║   Архив:    %-48s ║\n" "${FINAL_ARCHIVE}"
    printf "  ║   SHA-256:  %-48s ║\n" "${FINAL_CHECKSUM}"
    printf "  ║   Время:    %-48s ║\n" "$(date '+%Y-%m-%d %H:%M:%S %Z')"
    if [[ -n "${S3_BUCKET}" && "${SKIP_S3}" == "false" ]]; then
        printf "  ║   S3 URI:   s3://%-44s ║\n" "${S3_BUCKET}/${S3_PREFIX}/${BACKUP_ARCHIVE}"
    fi
    echo "  ║                                                              ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
else
    log_info "[DRY-RUN] Симуляция завершена. Никаких файлов не создано и не удалено."
fi

exit 0
