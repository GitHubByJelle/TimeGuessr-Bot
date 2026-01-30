# uv + Python preinstalled
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src

# 1) Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# 2) Install Python dependencies from lockfile
RUN uv sync --locked --no-install-project

# 3) Install Playwright Chromium
RUN uv run playwright install --with-deps chromium

# 4) Copy application source
COPY src/ /app/src/

# Conditionally copy .env if --build-arg DEV=1 is set
ARG DEV=0
RUN if [ "$DEV" = "1" ] && [ -f .env ]; then cp .env /app/.env; fi

# 5) Install the project itself (if applicable)
RUN uv sync --locked

# 6) Run your job
CMD ["uv", "run", "-m", "main"]
