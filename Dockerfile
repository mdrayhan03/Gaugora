FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GAUGORA_DATABASE_URL=sqlite:////data/gaugora.db \
    GAUGORA_HOST=0.0.0.0 \
    GAUGORA_PORT=8080 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY uv.lock ./

RUN uv sync --frozen --no-dev \
    && mkdir -p /data

EXPOSE 8080
VOLUME ["/data"]

CMD ["gaugora"]
