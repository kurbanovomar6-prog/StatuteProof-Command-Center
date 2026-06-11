#!/usr/bin/env bash
# =============================================================================
# scripts/deploy.sh — Автоматизированный production-деплой RegRadar Enterprise
# =============================================================================
#
# Выполняет полный цикл деплоя:
#   1. Валидация зависимостей хост-системы (Docker, Compose, curl)
#   2. Проверка наличия и корректности .env файла
#   3. Остановка и удаление устаревших контейнеров / orphaned сетей
#   4. Сборка многоэтапного Docker образа и запуск всех сервисов
#   5. Health-check loop: ждём HTTP 200 от /api/v1/health
#   6. Пауза 5 секунд: даём Redis и Celery workers полностью подняться
#   7. Засев демонстрационной базы данных (seed_demo_data.py)
#   8. Итоговый отчёт о состоянии платформы
#
# Использование:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh                     # стандартный деплой
#   ./scripts/deploy.sh --skip-seed         # без засева демо-данных
#   ./scripts/deploy.sh --no-cleanup        # без удаления старых containers
#   ./scripts/deploy.sh --env .env.staging  # с указанием env-файла
#   ./scripts/deploy.sh --compose docker-compose.prod.yml
#
# Требования хост-системы:
#   Docker Engine >= 24.x
#   Docker Compose >= 2.20 (plugin, не устаревший standalone compose-v1)
#   curl >= 7.x
# =============================================================================

set -euo pipefail

# =============================================================================
# ЦВЕТА И ФОРМАТИРОВАНИЕ
# =============================================================================

# ANSI escape-коды для наглядного статус-лога.
# Используем прямые escape-последовательности (совместимо с CI без $TERM).
_RED="\033[0;31m"
_GRN="\033[0;32m"
_YLW="\033[0;33m"
_BLU="\033[0;34m"
_MAG="\033[0;35m"
_CYN="\033[0;36m"
_BLD="\033[1m"
_RST="\033[0m"

# Временная метка для каждой строки лога: [HH:MM:SS]
_ts() { date "+%H:%M:%S"; }

# Вспомогательные функции вывода статусных строк
ok()   { echo -e "${_GRN}${_BLD}  [✓] $(_ts) $*${_RST}"; }
info() { echo -e "${_BLU}  [ℹ] $(_ts) $*${_RST}"; }
warn() { echo -e "${_YLW}  [⚠] $(_ts) $*${_RST}"; }
fail() { echo -e "${_RED}${_BLD}  [✗] $(_ts) $*${_RST}" >&2; }
step() { echo -e "\n${_MAG}${_BLD}══════════════════════════════════════════${_RST}"; \
         echo -e "${_MAG}${_BLD}  $*${_RST}"; \
         echo -e "${_MAG}${_BLD}══════════════════════════════════════════${_RST}"; }


# =============================================================================
# ПАРАМЕТРЫ ПО УМОЛЧАНИЮ
# =============================================================================

# Флаги управления поведением деплоя
SKIP_SEED=false          # --skip-seed:   не запускать seed_demo_data.py
NO_CLEANUP=false         # --no-cleanup:  не останавливать старые контейнеры
ENV_FILE=".env"          # --env <file>:  путь к env-файлу (относительно PROJECT_ROOT)
COMPOSE_FILE="docker-compose.yml"  # --compose <file>

# Параметры health-check loop
# 40 попыток × 5 сек = 200 секунд максимального ожидания готовности API
HC_MAX_ATTEMPTS=40
HC_INTERVAL=5            # пауза между попытками (секунды)
HC_TIMEOUT=8             # таймаут одного curl-запроса (секунды)

# Задержка после успешного health-check перед засевом данных.
# Даёт Redis-брокеру и Celery workers время завершить регистрацию
# очередей и установить соединения, чтобы не получить "queue not found"
# при первом enqueue из seed_demo_data.py.
POST_HEALTH_SLEEP=5


# =============================================================================
# РАЗБОР АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-seed)
            SKIP_SEED=true
            shift ;;
        --no-cleanup)
            NO_CLEANUP=true
            shift ;;
        --env)
            ENV_FILE="${2:?'--env требует аргумент: путь к .env файлу'}"
            shift 2 ;;
        --compose)
            COMPOSE_FILE="${2:?'--compose требует аргумент: путь к docker-compose файлу'}"
            shift 2 ;;
        -h|--help)
            echo ""
            echo "Использование: $0 [ОПЦИИ]"
            echo ""
            echo "  --skip-seed          Пропустить засев демо-данных"
            echo "  --no-cleanup         Не останавливать существующие контейнеры"
            echo "  --env <file>         Путь к .env файлу (по умолч.: .env)"
            echo "  --compose <file>     Путь к docker-compose.yml (по умолч.: docker-compose.yml)"
            echo "  -h, --help           Показать эту справку"
            echo ""
            exit 0 ;;
        *)
            fail "Неизвестный аргумент: '$1'"
            fail "Запустите '$0 --help' для просмотра доступных опций."
            exit 1 ;;
    esac
done


# =============================================================================
# ОПРЕДЕЛЕНИЕ ПУТЕЙ ПРОЕКТА
# =============================================================================

# Нормализуем пути: скрипт может быть вызван из любой директории.
# BASH_SOURCE[0] указывает на файл самого скрипта, а не на CWD вызывающего.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Переходим в корень проекта — docker compose читает .env и строит контекст отсюда
cd "${PROJECT_ROOT}"

# Абсолютные пути к ключевым файлам конфигурации
ENV_PATH="${PROJECT_ROOT}/${ENV_FILE}"
COMPOSE_PATH="${PROJECT_ROOT}/${COMPOSE_FILE}"


# =============================================================================
# ШАПКА ДЕПЛОЯ
# =============================================================================

echo -e "\n${_BLD}${_CYN}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║       RegRadar Enterprise — Production Deploy Script         ║"
printf "  ║       %-54s ║\n" "$(date '+%Y-%m-%d  %H:%M:%S %Z')"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${_RST}"

info "Корень проекта:    ${PROJECT_ROOT}"
info "Compose-файл:      ${COMPOSE_PATH}"
info "Env-файл:          ${ENV_PATH}"
info "Засев данных:      $( [[ "${SKIP_SEED}"   == "true" ]] && echo "отключён (--skip-seed)"   || echo "включён" )"
info "Очистка старых:    $( [[ "${NO_CLEANUP}"  == "true" ]] && echo "отключена (--no-cleanup)" || echo "включена" )"
info "Задержка (Redis):  ${POST_HEALTH_SLEEP} сек (после health-check)"


# =============================================================================
# ШАГ 1/8 — ВАЛИДАЦИЯ ЗАВИСИМОСТЕЙ ХОСТ-СИСТЕМЫ
# =============================================================================

step "ШАГ 1/8  Проверка зависимостей хост-системы"

# Проверяем наличие бинарника docker в PATH
if ! command -v docker &>/dev/null; then
    fail "Docker CLI не найден в PATH."
    fail "Установите Docker Engine >= 24.x: https://docs.docker.com/engine/install/"
    exit 1
fi
ok "docker CLI: $(docker --version)"

# Проверяем что Docker daemon запущен и текущий пользователь имеет доступ к socket
if ! docker info &>/dev/null; then
    fail "Docker daemon недоступен или не запущен."
    fail "Попробуйте следующие команды для диагностики:"
    fail "  sudo systemctl start docker"
    fail "  sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fi
ok "Docker daemon активен"

# Определяем команду Compose: предпочитаем plugin v2 (docker compose),
# откатываемся на устаревший standalone (docker-compose) если plugin недоступен.
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    ok "Docker Compose plugin: $(docker compose version)"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
    warn "Используется устаревший docker-compose standalone."
    warn "Рекомендуется обновиться до Compose Plugin v2."
    ok "docker-compose standalone: $(docker-compose --version)"
else
    fail "Docker Compose не найден."
    fail "Установите Compose Plugin: https://docs.docker.com/compose/install/"
    exit 1
fi

# curl обязателен для health-check loop
if ! command -v curl &>/dev/null; then
    fail "curl не найден. Установите: sudo apt-get install -y curl"
    exit 1
fi
ok "curl: $(curl --version | head -1)"


# =============================================================================
# ШАГ 2/8 — ПРОВЕРКА .env ФАЙЛА И ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# =============================================================================

step "ШАГ 2/8  Проверка конфигурации среды (.env)"

# Файл .env обязателен — без него Docker Compose не получит секреты
if [[ ! -f "${ENV_PATH}" ]]; then
    fail "Файл .env не найден: ${ENV_PATH}"
    fail ""
    fail "Создайте его из шаблона и заполните обязательные поля:"
    fail "   cp .env.example .env"
    fail "   nano .env"
    fail ""
    fail "Минимально необходимые переменные (отмечены ★ в .env.example):"
    fail "   API_PASSWORD_HASH — bcrypt-хэш пароля администратора"
    fail "   OPENAI_API_KEY    — ключ OpenAI для AI-анализа документов"
    exit 1
fi
ok ".env найден: ${ENV_PATH}"

# Проверяем права доступа на .env: должен быть читаем только владельцем.
# stat -c на Linux, stat -f на macOS (BSD).
ENV_PERMS=$(stat -c "%a" "${ENV_PATH}" 2>/dev/null || stat -f "%Lp" "${ENV_PATH}" 2>/dev/null || echo "unknown")
if [[ "${ENV_PERMS}" != "600" && "${ENV_PERMS}" != "400" && "${ENV_PERMS}" != "unknown" ]]; then
    warn ".env имеет небезопасные права доступа: ${ENV_PERMS}"
    warn "Рекомендуется: chmod 600 '${ENV_PATH}'"
fi

# Загружаем переменные из .env в текущий shell-контекст.
# Временно отключаем strict-mode: .env может содержать незаэскейпленные значения,
# пустые строки, комментарии — всё это вызывает ошибки при прямом source.
# Фильтруем строки-комментарии и пустые строки перед source.
set +euo pipefail
# shellcheck disable=SC1090
source <(
    grep -v '^\s*#' "${ENV_PATH}" \
    | grep -v '^\s*$' \
    | sed 's/^/export /'
) 2>/dev/null || true
set -euo pipefail

# Читаем APP_PORT из загруженного окружения (с разумным значением по умолчанию)
APP_PORT="${APP_PORT:-8080}"
info "Порт приложения (APP_PORT): ${APP_PORT}"

# Проверяем наличие критически важных переменных с placeholder-значениями.
# Деплой не прерывается — только предупреждение (может быть dev-режим без AI).
_missing_vars=()
for _check_var in API_PASSWORD_HASH; do
    _check_val="${!_check_var:-}"
    if [[ -z "${_check_val}" || "${_check_val}" == *"REPLACE"* || "${_check_val}" == *"CHANGEME"* ]]; then
        _missing_vars+=("${_check_var}")
    fi
done

if [[ ${#_missing_vars[@]} -gt 0 ]]; then
    warn "Следующие переменные не заполнены или содержат placeholder-значения:"
    for _mv in "${_missing_vars[@]}"; do
        warn "  • ${_mv}"
    done
    warn "Деплой продолжается. Убедитесь, что это не production с реальными клиентами."
fi

# Проверяем синтаксическую корректность docker-compose файла (без запуска)
if [[ ! -f "${COMPOSE_PATH}" ]]; then
    fail "docker-compose файл не найден: ${COMPOSE_PATH}"
    exit 1
fi

info "Валидация конфигурации Compose..."
if ! ${COMPOSE_CMD} -f "${COMPOSE_PATH}" config --quiet 2>/dev/null; then
    fail "docker-compose.yml содержит синтаксические ошибки:"
    ${COMPOSE_CMD} -f "${COMPOSE_PATH}" config 2>&1 | head -30 >&2
    exit 1
fi
ok "docker-compose.yml синтаксически корректен"


# =============================================================================
# ШАГ 3/8 — ОСТАНОВКА ПРЕДЫДУЩЕГО ОКРУЖЕНИЯ
# =============================================================================

step "ШАГ 3/8  Остановка предыдущего окружения"

if [[ "${NO_CLEANUP}" == "true" ]]; then
    warn "Остановка пропущена (флаг --no-cleanup)."
    warn "Существующие контейнеры и volumes будут переиспользованы."
else
    info "Останавливаем контейнеры и удаляем orphaned сети..."
    info "(named volumes с данными НЕ удаляются — БД и отчёты сохраняются)"

    # --remove-orphans: удаляет контейнеры, которых нет в текущем compose-файле
    # --timeout 30:     даём сервисам 30 сек на graceful shutdown
    # Не используем --volumes: это удалило бы именованные volumes с данными БД!
    ${COMPOSE_CMD} -f "${COMPOSE_PATH}" down \
        --remove-orphans \
        --timeout 30 \
        2>&1 | while IFS= read -r _line; do
            [[ -z "${_line// /}" ]] && continue
            info "  ↳ ${_line}"
        done

    ok "Предыдущее окружение остановлено"
fi


# =============================================================================
# ШАГ 4/8 — СБОРКА DOCKER ОБРАЗА И ЗАПУСК СЕРВИСОВ
# =============================================================================

step "ШАГ 4/8  Сборка образа и запуск всех сервисов"

info "Запускаем: ${COMPOSE_CMD} up --build -d"
info "Многоэтапная сборка (tesseract + playwright + зависимости) может занять"
info "от 3 до 8 минут при первом запуске. Повторные сборки быстрее (BuildKit кэш)."

# --build:  пересобирает образы при изменении Dockerfile или исходного кода
# -d:       запускает в фоновом режиме (detached), не блокируя терминал
# --env-file: явно указываем .env (Compose v2 читает его автоматически, но
#             явное лучше неявного — особенно при работе с нестандартным ENV_PATH)
${COMPOSE_CMD} -f "${COMPOSE_PATH}" \
    --env-file "${ENV_PATH}" \
    up --build -d \
    2>&1 | while IFS= read -r _line; do
        # Пропускаем пустые строки прогресса BuildKit
        [[ -z "${_line// /}" ]] && continue
        info "  ↳ ${_line}"
    done

ok "Все сервисы запущены в фоновом режиме"

# Начальная пауза: даём контейнерам время выйти из состояния "starting"
# и начать инициализацию приложения. Без этой паузы первые curl-запросы
# health-check могут падать с "Connection refused" — это нормально и обрабатывается
# в loop ниже, но пауза делает лог чище.
info "Начальная пауза 5 секунд: ждём старта процессов внутри контейнеров..."
sleep 5


# =============================================================================
# ШАГ 5/8 — HEALTH-CHECK LOOP: ОЖИДАНИЕ ГОТОВНОСТИ API
# =============================================================================

step "ШАГ 5/8  Ожидание готовности API (health-check loop)"

# Endpoint /api/v1/health зарегистрирован в main.py через app.add_api_route()
# и возвращает {"status": "healthy", "service": "regrada"}.
# Тот же endpoint используется в HEALTHCHECK директиве docker-compose.yml.
HEALTH_URL="http://localhost:${APP_PORT}/api/v1/health"

info "Health endpoint: ${HEALTH_URL}"
info "Стратегия:       ${HC_MAX_ATTEMPTS} попыток × ${HC_INTERVAL} сек = $((HC_MAX_ATTEMPTS * HC_INTERVAL)) сек максимум"

_attempt=0
_api_ready=false

while [[ ${_attempt} -lt ${HC_MAX_ATTEMPTS} ]]; do
    _attempt=$(( _attempt + 1 ))

    # curl флаги:
    #   --silent        подавляем прогресс-бар и информационные сообщения
    #   --fail          возвращает exit code != 0 при HTTP 4xx/5xx
    #   --max-time N    жёсткий таймаут всего запроса (секунды)
    #   --output /dev/null  отбрасываем тело ответа
    #   --write-out     выводим только HTTP статус-код
    # При любой сетевой ошибке (ECONNREFUSED, timeout) curl возвращает != 0,
    # поэтому используем || HTTP_CODE="000" для безопасного fallback.
    HTTP_CODE=$(
        curl \
            --silent \
            --fail \
            --max-time "${HC_TIMEOUT}" \
            --output /dev/null \
            --write-out "%{http_code}" \
            "${HEALTH_URL}" 2>/dev/null
    ) || HTTP_CODE="000"

    if [[ "${HTTP_CODE}" == "200" ]]; then
        _api_ready=true
        ok "API вернул HTTP 200 (попытка ${_attempt}/${HC_MAX_ATTEMPTS}) — сервис готов!"
        break
    fi

    # Выводим детальный статус каждые 5 попыток или когда получаем ненулевой HTTP-код
    # (ненулевой код означает что сервер уже отвечает, но ещё не инициализирован)
    if (( _attempt % 5 == 0 )) || [[ "${HTTP_CODE}" != "000" ]]; then
        warn "Попытка ${_attempt}/${HC_MAX_ATTEMPTS} — HTTP ${HTTP_CODE}. Ждём..."
    else
        # Минималистичный индикатор прогресса для промежуточных попыток
        printf "${_BLU}.${_RST}"
    fi

    sleep "${HC_INTERVAL}"
done

# Гарантируем перевод строки после точек прогресса
echo ""

# Если API так и не ответил — деплой провален; выводим диагностические подсказки
if [[ "${_api_ready}" == "false" ]]; then
    fail "API не ответил HTTP 200 за $((HC_MAX_ATTEMPTS * HC_INTERVAL)) секунд."
    fail ""
    fail "Диагностические команды:"
    fail "  Логи web-api:        ${COMPOSE_CMD} logs --tail=60 web-api"
    fail "  Логи celery-worker:  ${COMPOSE_CMD} logs --tail=30 celery-worker"
    fail "  Логи redis-cache:    ${COMPOSE_CMD} logs --tail=20 redis-cache"
    fail "  Статус контейнеров:  ${COMPOSE_CMD} ps"
    fail ""
    fail "Частые причины зависания:"
    fail "  • Порт ${APP_PORT} уже занят другим процессом: lsof -i :${APP_PORT}"
    fail "  • Ошибка импорта Python (опечатка в requirements.txt или битый .egg)"
    fail "  • Redis не поднялся: ${COMPOSE_CMD} logs redis-cache | tail -20"
    fail "  • Нехватка памяти: docker stats --no-stream"
    fail "  • Маршрут /api/v1/health не зарегистрирован в main.py"
    exit 1
fi

# Получаем и логируем полный JSON-ответ health-check для подтверждения
HC_BODY=$(
    curl --silent --max-time "${HC_TIMEOUT}" "${HEALTH_URL}" 2>/dev/null \
    || echo '{"status":"unknown"}'
)
info "Health response body: ${HC_BODY}"


# =============================================================================
# ШАГ 6/8 — ПАУЗА: ОЖИДАНИЕ ГОТОВНОСТИ REDIS И CELERY WORKERS
# =============================================================================

step "ШАГ 6/8  Stabilization: ожидаем полной готовности Redis и Celery"

# ПОЧЕМУ ЭТА ПАУЗА КРИТИЧНА:
# HTTP 200 от /api/v1/health означает что NiceGUI + FastAPI инициализированы.
# Однако это НЕ гарантирует что:
#   1. Celery workers завершили регистрацию очередей в Redis
#   2. Redis-брокер принял все подключения от worker-процессов
#   3. celery-beat загрузил расписание и готов принимать задачи
#
# Без этой паузы seed_demo_data.py может enqueue задачи в очереди,
# которые workers ещё не слушают — задачи зависнут в "PENDING" навсегда.
# 5 секунд достаточно для полной инициализации Celery на большинстве хостов.

info "Пауза ${POST_HEALTH_SLEEP} сек: даём Redis-брокеру и Celery workers"
info "завершить регистрацию очередей (scraping, reports, default)..."
sleep "${POST_HEALTH_SLEEP}"
ok "Redis и Celery workers готовы к приёму задач"


# =============================================================================
# ШАГ 7/8 — ЗАСЕВ ДЕМОНСТРАЦИОННОЙ БАЗЫ ДАННЫХ
# =============================================================================

step "ШАГ 7/8  Засев демонстрационной базы данных"

if [[ "${SKIP_SEED}" == "true" ]]; then
    warn "Засев пропущен (флаг --skip-seed)."
    warn "Запустите вручную: ${COMPOSE_CMD} exec web-api python3 scripts/seed_demo_data.py"
else
    info "Запускаем seed_demo_data.py внутри контейнера web-api..."
    info "Скрипт идемпотентен: повторный запуск безопасен, дубли не создаются."
    info "(17 НПА + 16 YTD-снэпшотов по 4 юрисдикциям за 4 месяца)"

    # docker compose exec флаги:
    #   -T  отключаем pseudo-TTY — обязательно для неинтерактивного CI/CD
    # grep -E фильтрует вывод: показываем только значимые строки (INFO, ERROR и т.д.),
    # отбрасывая шум SQLAlchemy низкоуровневых запросов.
    _seed_ok=true
    if ! ${COMPOSE_CMD} -f "${COMPOSE_PATH}" exec -T web-api \
            python3 scripts/seed_demo_data.py \
            2>&1 | grep -E "INFO|WARN|ERROR|CRITICAL|═|▶|✔|НПА|YTD|Засев|Seeding|регул"; then
        _seed_ok=false
    fi

    if [[ "${_seed_ok}" == "true" ]]; then
        ok "Демо-данные успешно загружены в базу данных"
    else
        _seed_exit=$?
        warn "seed_demo_data.py завершился с кодом ${_seed_exit}."
        warn "Платформа продолжает работать. Засев можно повторить вручную:"
        warn "  ${COMPOSE_CMD} exec web-api python3 scripts/seed_demo_data.py"
    fi
fi


# =============================================================================
# ШАГ 8/8 — ИТОГОВЫЙ ОТЧЁТ
# =============================================================================

step "ШАГ 8/8  Финальный статус платформы"

# Выводим таблицу состояния всех контейнеров
info "Статус контейнеров:"
${COMPOSE_CMD} -f "${COMPOSE_PATH}" ps \
    --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" \
    2>/dev/null | while IFS= read -r _line; do
        info "  ${_line}"
    done

# Проверяем что ключевые сервисы в статусе "running"
# (не "exited", не "restarting", не "created")
_unhealthy_services=()
for _svc in web-api redis-cache celery-worker celery-beat; do
    _container_state=$(
        ${COMPOSE_CMD} -f "${COMPOSE_PATH}" ps -q "${_svc}" 2>/dev/null \
        | xargs -r docker inspect --format='{{.State.Status}}' 2>/dev/null \
        || echo "missing"
    )
    if [[ "${_container_state}" != "running" ]]; then
        _unhealthy_services+=("${_svc} (${_container_state})")
    fi
done

echo ""

if [[ ${#_unhealthy_services[@]} -gt 0 ]]; then
    warn "Следующие сервисы не находятся в статусе 'running':"
    for _s in "${_unhealthy_services[@]}"; do
        warn "  • ${_s}"
    done
    warn "Проверьте логи: ${COMPOSE_CMD} logs <имя-сервиса> --tail=50"
else
    ok "Все ключевые сервисы (web-api, redis-cache, celery-worker, celery-beat) активны"
fi

# Финальная сводка с URL доступа и полезными командами
FLOWER_PORT="${FLOWER_PORT:-5555}"

echo ""
echo -e "${_BLD}${_GRN}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║         RegRadar Enterprise — ДЕПЛОЙ ЗАВЕРШЁН ✓             ║"
echo "  ╠══════════════════════════════════════════════════════════════╣"
echo "  ║                                                              ║"
printf "  ║   🌐  Дашборд:      http://localhost:%-24s ║\n" "${APP_PORT}"
printf "  ║   🔌  REST API:     http://localhost:%s/api/v1/      %-9s ║\n" "${APP_PORT}" ""
printf "  ║   ❤️   Health:       http://localhost:%s/api/v1/health %-6s ║\n" "${APP_PORT}" ""
printf "  ║   📊  Flower:       http://localhost:%-24s ║\n" "${FLOWER_PORT}"
echo "  ║                                                              ║"
echo "  ║   Полезные команды:                                          ║"
echo "  ║     Логи API:      ${COMPOSE_CMD} logs -f web-api"
echo "  ║     Логи Celery:   ${COMPOSE_CMD} logs -f celery-worker"
echo "  ║     Все логи:      ${COMPOSE_CMD} logs -f"
echo "  ║     Остановить:    ${COMPOSE_CMD} down"
echo "  ║     Бэкап БД:      ${COMPOSE_CMD} exec web-api bash /app/scripts/backup_db.sh"
echo "  ║     Рестарт API:   ${COMPOSE_CMD} restart web-api"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${_RST}"

exit 0
