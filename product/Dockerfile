# =============================================================================
# Dockerfile — RegRadar Enterprise  v2.2
# =============================================================================
#
# Two-stage build:
#   builder  — compiles Python C-extensions; discarded from final image
#   runtime  — minimal production image (~650 MB with Playwright Chromium)
#
# Key design decisions:
#   • "playwright install --with-deps chromium" lets Playwright manage its own
#     system-library list (libnss3, libatk, etc.) independently of our manual
#     apt-get.  This means the dep list stays correct across Playwright upgrades
#     without us touching the Dockerfile.
#   • No "|| echo" fallback on playwright install — a failed browser download
#     must break the build visibly, not produce a container that crashes at
#     runtime with an opaque "Executable doesn't exist" error.
#   • All Playwright browser files are chowned to regrada in the same RUN layer
#     as the install, so USER regrada can execute the binary at runtime.
#   • PLAYWRIGHT_BROWSERS_PATH is baked into the image; no Railway env var needed.
#
# Build:  docker build -t regrada:latest .
# Run:    docker run -p 8080:8080 --env-file .env regrada:latest
# =============================================================================


# ── Stage 1: dependency compiler ─────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

LABEL stage="builder"

# Build-only system libs for Python C-extensions (not copied to runtime image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        libpq-dev \
        libpoppler-cpp-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Layer cache: only invalidated when requirements.txt changes
COPY requirements.txt .

RUN pip install --upgrade pip wheel setuptools --quiet && \
    pip install \
        --prefix=/install \
        --no-cache-dir \
        -r requirements.txt


# ── Stage 2: production runtime ───────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="RegRadar Enterprise" \
      org.opencontainers.image.description="Autonomous Regulatory Intelligence Platform" \
      org.opencontainers.image.version="2.2.0" \
      org.opencontainers.image.vendor="RegRadar" \
      org.opencontainers.image.licenses="Proprietary"

# ── Non-Playwright system dependencies ───────────────────────────────────────
# Playwright manages its own chromium runtime libs via --with-deps below.
# This layer covers OCR, PDF processing, fonts, and SSL only.
RUN apt-get update && apt-get install -y --no-install-recommends \
        \
        # OCR engine + CIS language packs
        tesseract-ocr \
        tesseract-ocr-rus \
        tesseract-ocr-eng \
        \
        # PDF processing (pdfplumber C backend)
        poppler-utils \
        libpoppler-cpp0v5 \
        \
        # Fonts for PDF report generation (fpdf2)
        fonts-liberation \
        fonts-dejavu-core \
        fonts-freefont-ttf \
        fonts-noto \
        \
        # Runtime utilities
        libmagic1 \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ── Compiled Python packages from builder ─────────────────────────────────────
COPY --from=builder /install /usr/local

# ── Non-root service account ──────────────────────────────────────────────────
RUN groupadd --gid 1001 regrada && \
    useradd \
        --uid 1001 \
        --gid regrada \
        --no-create-home \
        --shell /sbin/nologin \
        --comment "RegRadar service account" \
        regrada

# ── Application source ────────────────────────────────────────────────────────
WORKDIR /app
COPY --chown=regrada:regrada . .

# ── Persistent data directories ───────────────────────────────────────────────
# Mounted as named volumes in docker-compose; created here so mount doesn't
# reset ownership.
RUN mkdir -p \
        /app/data \
        /app/reports \
        /app/backups \
        /app/logs \
        /app/snapshots \
        /app/keys && \
    chmod +x /app/entrypoint.sh

# ── Playwright Chromium installation ─────────────────────────────────────────
# Runs as root so apt-get (--with-deps) can install chromium's system libs.
# chown at the end transfers all browser files to regrada before USER switch.
# No "|| echo" — a failed install must break the build, not produce a broken image.
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers

RUN mkdir -p /app/.playwright-browsers && \
    python -m playwright install --with-deps chromium && \
    chown -R regrada:regrada \
        /app/.playwright-browsers \
        /app/data \
        /app/logs \
        /app/reports \
        /app/backups \
        /app/snapshots \
        /app/keys

# ── Switch to non-root user ───────────────────────────────────────────────────
USER regrada

# ── Runtime environment ───────────────────────────────────────────────────────
ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata \
    PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers \
    PORT=8080

EXPOSE 8080

# ── Health check ──────────────────────────────────────────────────────────────
# start-period=90s: NiceGUI + SQLAlchemy schema migration takes longer than Flask.
# Uses ${PORT} so the check adapts when Railway overrides the port.
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=90s \
    --retries=3 \
    CMD curl --silent --fail --max-time 8 \
        "http://localhost:${PORT}/api/v1/health" || exit 1

# ── Default entrypoint (web service) ─────────────────────────────────────────
# Railway Celery worker overrides this via startCommand in the Railway dashboard
# or via the Procfile worker process type.
CMD ["python", "main.py"]
