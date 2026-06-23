# StatuteProof / RegRadar — Production Dockerfile
#
# Build:  docker build -t statuteproof .
# Run:    docker run -p 8080:8080 --env-file .env statuteproof
#
# .dockerignore should exclude: .env, __pycache__, *.pyc, tests/, data/,
# logs/, node_modules/, web/dist/, *.md, .git/
#
# Python version matches the minimum enforced in run.py (3.11+).

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
# These cover:
#   - BeautifulSoup / lxml HTML parsing (libxml2 is bundled in lxml wheel, but
#     libxslt is needed for some lxml builds on slim)
#   - Playwright / Chromium runtime: the full list below is the minimal Debian
#     package set required to run Chromium headless on a slim image.
#   - ca-certificates: allows HTTPS requests to succeed inside the container.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies (layer-cached separately from source) ─────────────────
# Copy requirements first so Docker can cache the pip install layer.
# The layer is only invalidated when requirements.txt changes — not on every
# source code edit.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ── Playwright Chromium binary ─────────────────────────────────────────────────
# --with-deps installs any remaining OS-level deps that playwright needs beyond
# what we installed above (belt-and-suspenders approach).
RUN playwright install chromium --with-deps

# ── Application source ────────────────────────────────────────────────────────
# Copy everything else after deps are installed to maximise cache reuse.
COPY . .

# ── Runtime directories ────────────────────────────────────────────────────────
# Pre-create directories that the app writes to so they are owned by root
# (or whatever user you switch to) and don't fail on first write.
RUN mkdir -p logs data/backups

# ── Port ──────────────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Default command ───────────────────────────────────────────────────────────
# Starts the FastAPI/uvicorn API server. Override CMD (or pass a Railway
# startCommand) to run other sub-commands such as `python run.py watch`.
CMD ["python", "run.py", "api"]
