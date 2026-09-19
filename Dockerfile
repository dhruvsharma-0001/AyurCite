# Multi-stage Dockerfile for AyurCite v1
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install uv for ultra-fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml .
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache \
    fastapi uvicorn pydantic rank-bm25 psutil httpx pandas

# Final runner stage
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

COPY --from=builder /opt/venv /opt/venv
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "src.ayurcite.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
