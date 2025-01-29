FROM --platform=$TARGETPLATFORM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_PREFER_BINARY=1
ENV CMAKE_ARGS="-DONNX_USE_PROTOBUF_SHARED_LIBS=OFF -DDOWNLOAD_EXTRACT_TIMESTAMP=ON -Wno-dev -DCMAKE_POLICY_DEFAULT_CMP0148=NEW -DCMAKE_POLICY_DEFAULT_CMP0135=NEW"
ENV CFLAGS="-O2"
ENV CXXFLAGS="-O2"

WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    CMAKE_ARGS="-DONNX_USE_PROTOBUF_SHARED_LIBS=OFF" \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder --chown=app:app /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV MODEL_CACHE_DIR=/app/model_cache

RUN useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser
CMD ["uv", "run", "fastapi", "run", "./src/api.py", "--host", "0.0.0.0", "--port", "8000"]