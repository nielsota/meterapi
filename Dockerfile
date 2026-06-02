# syntax=docker/dockerfile:1
# Multi-stage image: install with uv, run a slim Python runtime (App Runner + local).
# Build for AWS (linux/amd64): docker build --platform linux/amd64 -t meterapi .

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app /app

# App Runner sets PORT (commonly 8080). Local: docker run -p 8000:8000 -e PORT=8000 ...
EXPOSE 8000

CMD ["/bin/sh", "-c", "exec uvicorn meterapi.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
